from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import datetime
from pyecharts.charts import Bar
from pyecharts import options as opts

from appdef import app, conn

########################################################
from appdef import validateDates
########################################################

def authenticateAgent():
    username = ""
    try:
        #could be that there is no user, make sure
        username = session['username']
    except:
        return False
    
    cursor = conn.cursor()
    query = 'select * from booking_agent where email=%s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if data:
        return True
    else:
        #Logout before returning error message
        session.pop('username')
        return False

@app.route('/agentHome')
def agentHome():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * \
    FROM purchases, ticket, flight, booking_agent \
    WHERE purchases.ticket_id = ticket.ticket_id \
    AND ticket.airline_name = flight.airline_name \
    AND ticket.flight_num = flight.flight_num \
    AND booking_agent.email = %s AND booking_agent.booking_agent_id = purchases.booking_agent_id \
    AND departure_time > curdate() \
    ORDER BY customer_email'
    cursor.execute(query, (username))
    data = cursor.fetchall()

    # Get booking_agent_id
    queryGetID = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor.execute(queryGetID, username)
    agentID = cursor.fetchone()
    # Get total commsion in the past 30 days
    queryGetCommission = 'SELECT sum(price)*.10 as totalComm FROM purchases, ticket, flight \
                          WHERE purchases.ticket_id = ticket.ticket_id \
                          AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
                          AND purchases.purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE() \
                          AND purchases.booking_agent_id = %s'
    cursor.execute(queryGetCommission, agentID['booking_agent_id'])
    totalComm = cursor.fetchone()
    totalCommVal = 0
    if totalComm['totalComm'] != None:
      totalCommVal = totalComm['totalComm']
    # print totalComm 
    # Get total tickets in the past 30 days 
    queryGetTicketCount = 'SELECT count(*) as ticketCount FROM purchases, ticket, flight \
                          WHERE purchases.ticket_id = ticket.ticket_id \
                          AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
                          AND purchases.purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE() \
                          AND purchases.booking_agent_id = %s'
    cursor.execute(queryGetTicketCount, agentID['booking_agent_id'])
    ticketCount = cursor.fetchone()
    ticketCountVal = ticketCount['ticketCount']
    avgComm = 0
    # print ticketCount, totalCommVal
    if ticketCountVal != 0:
      avgComm = totalCommVal/ticketCountVal

    cursor.close()  

    ###################################################################################
    error = request.args.get('error')
    return render_template('agent.html', username=username, posts=data, 
                            totalComm=totalCommVal, avgComm=avgComm, ticketCount=ticketCountVal,error = error)      
    #######################################################################################
@app.route('/agentUpcomingFlights', methods=['GET', 'POST'])
def agentUpcomingFlights():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor = conn.cursor()
    if request.method == 'POST':
      city = request.form.get('citysearchbox', False)
      if city:
        query = 'SELECT * \
            FROM purchases, ticket, flight, booking_agent, airport \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name \
            AND ticket.flight_num = flight.flight_num \
            AND (flight.arrival_airport = airport_name or flight.departure_airport = airport_name)\
            AND booking_agent.email = %s AND booking_agent.booking_agent_id = purchases.booking_agent_id \
            AND airport.airport_city = %s\
            AND departure_time > curdate() \
            ORDER BY customer_email'
        cursor.execute(query, (username, city))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('agentUpcomingFlights.html', username=username, posts=data)    

      airport = request.form.get('airportsearchbox', False)
      if airport:
        query = 'SELECT * \
            FROM purchases, ticket, flight, booking_agent \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name \
            AND ticket.flight_num = flight.flight_num \
            AND (flight.arrival_airport = %s or flight.departure_airport = %s)\
            AND booking_agent.email = %s AND booking_agent.booking_agent_id = purchases.booking_agent_id \
            AND departure_time > curdate() \
            ORDER BY customer_email'
        cursor.execute(query, (airport, airport, username))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('agentUpcomingFlights.html', username=username, posts=data)    
      
      begintime = request.form["begintime"]
      endtime = request.form["endtime"]
    
      if datetime.datetime.strptime(begintime, "%Y-%m-%d") > datetime.datetime.strptime(endtime, "%Y-%m-%d"):
        return render_template('viewUpcomingFlights.html', username=username, error="The dates you entered are invalid.")
      else:
        query = 'SELECT * \
            FROM purchases, ticket, flight, booking_agent \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name \
            AND ticket.flight_num = flight.flight_num \
            AND booking_agent.email = %s AND booking_agent.booking_agent_id = purchases.booking_agent_id \
            AND departure_time > curdate()\
            and ((date(flight.departure_time) between %s and %s) or (date(flight.arrival_time) between %s and %s))\
            ORDER BY customer_email;'
        cursor.execute(query, (username, begintime, endtime, begintime, endtime))
        data = cursor.fetchall()
        cursor.close()  
        return render_template('agentUpcomingFlights.html', username=username, posts=data)    

    
    query = 'SELECT * \
            FROM purchases, ticket, flight, booking_agent \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name \
            AND ticket.flight_num = flight.flight_num \
            AND booking_agent.email = %s AND booking_agent.booking_agent_id = purchases.booking_agent_id \
            AND departure_time > curdate() \
            ORDER BY customer_email'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()  
    return render_template('agentUpcomingFlights.html', username=username, posts=data)    

@app.route('/searchPageAgent')
def searchPageAgent():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    return render_template('searchAgent.html',username = username)

@app.route('/searchAgent', methods=['POST'])
def searchAgent():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor = conn.cursor()
    fromcity = request.form['fromcity']
    fromairport = request.form['fromairport']
    fromdate = request.form['fromdate']
    tocity = request.form['tocity']
    toairport = request.form['toairport']
    todate = request.form['todate']
    # Get booking_agent_id
    queryGetID = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor.execute(queryGetID, username)
    agentID = cursor.fetchone()['booking_agent_id']
    # Main query  
    query = "SELECT * FROM flight, airport, purchases, ticket \
            WHERE airport.airport_name=flight.departure_airport \
            AND flight.flight_num = ticket.flight_num AND flight.airline_name = ticket.airline_name\
            AND ticket.ticket_id = purchases.ticket_id\
            AND purchases.booking_agent_id = %s\
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            -- AND flight.status = 'Upcoming'\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
              (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
              WHERE airport.airport_name=flight.arrival_airport \
              AND airport.airport_city = %s \
              AND airport.airport_name = %s)"
    cursor.execute(query, (agentID, fromcity, fromairport,fromdate, todate, tocity, toairport))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if(data):
      return render_template('searchAgent.html', results=data)
    else:
      #returns an error message to the html page
      error = 'No results found'
      return render_template('searchAgent.html', error=error)   

@app.route('/commission', methods=['POST'])
def commission():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor = conn.cursor()
    fromdate = request.form['fromdate']
    todate = request.form['todate']
    # print(fromdate, todate)
    ####################################################################
    if not validateDates(fromdate,todate):
      error = "Invalid Time Range"
      return redirect(url_for('agentHome',error = error))
    ###################################################################

    # Get booking_agent_id
    queryGetID = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor.execute(queryGetID, username)
    agentID = cursor.fetchone()
    # print('~~~DEBUG: ', agentID)
    # Get total commsion in the past 30 days
    queryGetCommission = 'SELECT sum(price)*.10 as totalComm FROM purchases, ticket, flight \
                          WHERE purchases.ticket_id = ticket.ticket_id \
                          AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
                          AND purchases.purchase_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
                          AND purchases.booking_agent_id = %s'
    cursor.execute(queryGetCommission, (fromdate, todate, agentID['booking_agent_id']))
    totalComm = cursor.fetchone()
    totalCommVal = 0
    if totalComm['totalComm'] != None:
      totalCommVal = totalComm['totalComm']
    # print('~~~DEBUG:: ', totalComm)
    # Get total tickets in the past 30 days 
    queryGetTicketCount = 'SELECT count(*) as ticketCount FROM purchases, ticket, flight \
                          WHERE purchases.ticket_id = ticket.ticket_id \
                          AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
                          AND purchases.purchase_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
                          AND purchases.booking_agent_id = %s'
    cursor.execute(queryGetTicketCount, (fromdate, todate, agentID['booking_agent_id']))
    ticketCount = cursor.fetchone()
    ticketCountVal = ticketCount['ticketCount']  
    # print('~~~DEBUG: ', ticketCount)
    # avgComm = totalComm/ticketCount
    cursor.close()
    return render_template('commission.html', username = username, fromdate=fromdate, todate=todate, totalComm=totalCommVal, ticketCount=ticketCountVal)

@app.route('/viewTopCustomer')
def viewTopCustomer():
  if not authenticateAgent():
    error = 'Invalid Credentials'
    return redirect(url_for('errorpage', error=error))
  else:
    username = session['username']
    cursor1 = conn.cursor()
    queryGetID = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor1.execute(queryGetID, username)
    agentID = cursor1.fetchone()['booking_agent_id']
    query1 = "select count(ticket_id) as cnt,customer_email \
            from purchases \
            where booking_agent_id = %s\
            and purchase_date between DATE_SUB(curdate(), INTERVAL 6 MONTH) and curdate()\
            group by customer_email\
            order by cnt DESC limit 5"
    cursor1.execute(query1,agentID)
    data1 = cursor1.fetchall()
    cursor1.close()
    error = None

    c1 = (
        Bar()
            .add_xaxis([d['customer_email'] for d in data1])
            .add_yaxis('total ticket number',[d['cnt'] for d in data1])
            .set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-25)),
                            title_opts=opts.TitleOpts(title="Top Ticket Amount",
                            subtitle= "In the past 6 months"))
    )

    cursor2 = conn.cursor()
    query2 = "SELECT sum(price)*.10 as totalComm, purchases.customer_email FROM purchases, ticket, flight\
              WHERE purchases.ticket_id = ticket.ticket_id\
              AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num\
              AND purchases.purchase_date BETWEEN DATE_SUB(curdate(), INTERVAL 1 YEAR) and curdate() \
              AND purchases.booking_agent_id = %s\
              group by purchases.customer_email\
              order by totalComm DESC limit 5"
    cursor2.execute(query2,agentID)
    data2 = cursor2.fetchall()
    cursor2.close()
    c2 = (
        Bar()
            .add_xaxis([d['customer_email'] for d in data2])
            .add_yaxis('Total Commision',[d['totalComm'] for d in data2])
            .set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-25)),
                            title_opts=opts.TitleOpts(title="Top Commision Amount",subtitle= "In the past 1 year"))
    )

    if data1 and data2:
        return render_template('viewTopCustomer.html',username = username,
                                bar_options1 = c1.dump_options(),
                                bar_options2 = c2.dump_options())
    else:
        error = 'Sorry! No data available Right Now.'
        return render_template('viewTopCustomer.html',username=username, error = error)







