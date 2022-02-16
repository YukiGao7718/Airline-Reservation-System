from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import datetime
from pyecharts.charts import Bar
from pyecharts import options as opts

from appdef import *

def authenticateCustomer():
    username = ""
    try:
        #could be that there is no user, make sure
        username = session['username']
    except:
        return False
    
    cursor = conn.cursor()
    query = 'select * from customer where email=%s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if data:
        return True
    else:
        #Logout before returning error message
        session.pop('username')
        return False

@app.route('/customerHome')
def customerHome():
  if not authenticateCustomer():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
    FROM purchases, ticket, flight \
    WHERE purchases.ticket_id = ticket.ticket_id \
    AND ticket.airline_name = flight.airline_name \
    AND ticket.flight_num = flight.flight_num \
    AND customer_email = %s AND departure_time > curdate()'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()  
    return render_template('customer.html', username=username, posts=data)    

@app.route('/viewUpcomingFlights', methods=['GET', 'POST'])
def viewUpcomingFlights():
  if authenticateCustomer():
    username = session['username']
    cursor = conn.cursor()
    if request.method == 'POST':
      city = request.form.get('citysearchbox', False)
      if city:
        query='SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
                FROM purchases, ticket, flight, airport \
                WHERE purchases.ticket_id = ticket.ticket_id \
                AND ticket.airline_name = flight.airline_name \
                AND ticket.flight_num = flight.flight_num \
                AND (flight.arrival_airport = airport_name or flight.departure_airport = airport_name)\
                AND airport.airport_city = %s\
                AND customer_email = %s AND departure_time > curdate();'
        cursor.execute(query, (city, username))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('viewUpcomingFlights.html', username=username, posts=data)    

      airport = request.form.get('airportsearchbox', False)
      ##########################################################################
      error = request.args.get('error')
      if len(airport)>3:
        error = "Please enter the abbreviation of airport name."
        return render_template('viewUpcomingFlights.html',error = error)
      cursor = conn.cursor()
      query1 = "select * from airport where airport_name = %s"
      cursor.execute(query1,airport)
      data1 = cursor.fetchall()
      cursor.close()
      if not data1:
        error = " The airport doesn't exist."
        return render_template('viewUpcomingFlights.html',error = error)
      ##########################################################################
      if airport:
        query='SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
                FROM purchases, ticket, flight\
                WHERE purchases.ticket_id = ticket.ticket_id \
                AND ticket.airline_name = flight.airline_name \
                AND ticket.flight_num = flight.flight_num \
                AND (flight.arrival_airport = %s or flight.departure_airport = %s)\
                AND customer_email = %s AND departure_time > curdate();'
        cursor.execute(query, (airport, airport, username))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('viewUpcomingFlights.html', username=username, posts=data)    
      
      begintime = request.form["begintime"]
      endtime = request.form["endtime"]
    
      if datetime.datetime.strptime(begintime, "%Y-%m-%d") > datetime.datetime.strptime(endtime, "%Y-%m-%d"):
        return render_template('viewUpcomingFlights.html', username=username, error="The dates you entered are invalid.")
      else:
        query="SELECT distinct purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
              FROM purchases, ticket, flight\
              WHERE purchases.ticket_id = ticket.ticket_id \
              AND ticket.airline_name = flight.airline_name \
              AND ticket.flight_num = flight.flight_num \
              AND purchases.customer_email = %s \
              AND flight.departure_time > curdate()\
              and ((date(flight.departure_time) between %s and %s) or (date(flight.arrival_time) between %s and %s));"
        cursor.execute(query, (username, begintime, endtime, begintime, endtime))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('viewUpcomingFlights.html', username=username, posts=data)    

    
    query = 'SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
            FROM purchases, ticket, flight \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name \
            AND ticket.flight_num = flight.flight_num \
            AND customer_email = %s AND departure_time > curdate();'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()  
    return render_template('viewUpcomingFlights.html', username=username, posts=data)    
  else:
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))

@app.route('/searchPageCustomer')
def searchPageCustomer():
  if authenticateCustomer():
    return render_template('searchCustomer.html')
  else:
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))

@app.route('/searchCustomer', methods=['POST'])
def searchCustomer():
  if authenticateCustomer():
    username = session['username']
    cursor = conn.cursor()
    fromcity = request.form['fromcity']
    fromairport = request.form['fromairport']
    fromdate = request.form['fromdate']
    tocity = request.form['tocity']
    toairport = request.form['toairport']
    todate = request.form['todate']
    ##############################################################
    if datetime.datetime.strptime(fromdate, "%Y-%m-%d") > datetime.datetime.strptime(todate, "%Y-%m-%d"):
        return render_template('searchCustomer.html', error="The dates you entered are invalid.")
    ##############################################################
    query = 'SELECT * FROM flight, airport, purchases, ticket \
            WHERE airport.airport_name=flight.departure_airport \
            AND flight.flight_num = ticket.flight_num AND flight.airline_name = ticket.airline_name\
            AND ticket.ticket_id = purchases.ticket_id\
            AND purchases.customer_email = %s\
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            # AND flight.status = "Upcoming"\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
              (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
              WHERE airport.airport_name=flight.arrival_airport \
              AND airport.airport_city = %s \
              AND airport.airport_name = %s)'
    cursor.execute(query, (username, fromcity, fromairport, fromdate, todate, tocity, toairport))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if(data):
      return render_template('searchCustomer.html', username=username, results=data)
    else:
      #returns an error message to the html page
      error = 'No results found'
      return render_template('searchCustomer.html', error=error)  
  else:
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))

@app.route('/trackMySpending', methods=['GET', 'POST'])
def trackMySpending():
  if not authenticateCustomer():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    if request.method == 'POST':
          to_date = request.form['to_date']
          from_date = request.form['from_date']
          if datetime.datetime.strptime(from_date, "%Y-%m-%d") > datetime.datetime.strptime(to_date, "%Y-%m-%d"):
              return render_template('viewCustomerSpending.html', error="The dates you entered are invalid.")
          to_date_format = datetime.datetime.strptime(to_date, '%Y-%m-%d')
          from_date_format = datetime.datetime.strptime(from_date, '%Y-%m-%d')
          year = to_date_format.year
          month = to_date_format.month
          date = to_date_format.day
          from_year = from_date_format.year
          from_month = from_date_format.month
          from_date_date = from_date_format.day
          from_date_string = '{}-{}-{}'.format(from_year, from_month, from_date_date)
          to_date_string = '{}-{}-{}'.format(year, month, date)
          monthnum = (year - from_year)*12 + month - from_month
    else:
          to_date = datetime.datetime.now()
          year = to_date.year
          month = to_date.month
          if month-6 < 0:
            from_month = 12 + (month-6)
            from_year = to_date.year - 1
          else:
            from_month = month-6
            from_year = year
          date = to_date.day
          monthnum = 5
          string = '{} 1 {} 00:00'.format(month, from_year)
          from_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
          from_date_string = '{}-{}-{}'.format(from_year, from_month, date)
          to_date_string = '{}-{}-{}'.format(year, month, date)

    cursor = conn.cursor()
    sumPrice = 'SELECT COALESCE(sum(flight.price),0) as sum\
              FROM purchases,ticket,flight\
              WHERE purchases.customer_email = %s\
              AND ticket.ticket_id = purchases.ticket_id\
              and ticket.flight_num = flight.flight_num\
              and ticket.airline_name = flight.airline_name\
              and purchases.purchase_date >= %s\
              and purchases.purchase_date <= %s;'
    cursor.execute(sumPrice, (username, from_date_string, to_date_string ))
    sumSpending = float(cursor.fetchone()['sum'])

    if month < 12:
        string = '{} 1 {} 00:00'.format(month+1, year + 1)
    else:
        string = '{} 1 {} 00:00'.format(1, year + 2)
    temp_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
    
    labels = []
    values = []
    temp_year = year
    temp_month = month
    for i in range(0,monthnum + 1):
        this_date = temp_date
        this_month = temp_month
        temp_month = (month-i)%12
        if temp_month == 0:
            temp_month = 12
        if temp_month > this_month:
            temp_year = temp_year - 1
        string = '{} 1 {} 00:00'.format(temp_month, temp_year)
        temp_date = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
        query = 'SELECT COALESCE(sum(flight.price),0) as sum_month\
              FROM purchases,ticket,flight\
              WHERE purchases.customer_email = %s\
              AND ticket.ticket_id = purchases.ticket_id\
              and ticket.flight_num = flight.flight_num\
              and ticket.airline_name = flight.airline_name\
              and purchases.purchase_date > %s\
              and purchases.purchase_date < %s;'
        cursor.execute(query, (username, temp_date, this_date, ))
        data = cursor.fetchone()
        label = '{}-{}'.format(temp_year, temp_month)
        labels.append(label)
        values.append(float(data['sum_month']))
    cursor.close()
    labels.reverse()
    values.reverse()
    try:
        mymax = max(values)
    except:
        mymax = 100
    return render_template('viewCustomerSpending.html', username=username, sumSpending = sumSpending, max = mymax, from_date = from_date_string, to_date = to_date_string, labels=labels, values=values)
 