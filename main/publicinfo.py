from flask import Flask, render_template, request, redirect, url_for
import pymysql.cursors
import time

from appdef import *

@app.route('/search')
def searchpage():
    error = request.args.get('error')
    return render_template('search.html', error=error)

@app.route('/searchFlights/city', methods=['POST'])
def searchForCity():
    cursor = conn.cursor()
    searchtext = request.form['citysearchbox']
    query = 'select * from flight,airport where (airport.airport_name=flight.departure_airport or airport.airport_name=flight.arrival_airport) and airport.airport_city=%s and (departure_time >= curtime() or arrival_time >= curtime())'
    # query = 'select * from flight,airport where (airport.airport_name=flight.departure_airport or airport.airport_name=flight.arrival_airport) and airport.airport_city=%s'
    cursor.execute(query, (searchtext))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if data:
        return render_template('searchFlights.html', results=data)
    else:
        #returns an error message to the html page
        error = 'No results found'
        return redirect(url_for('searchpage', error=error))

@app.route('/searchFlights/airport', methods=['POST'])
def searchForAirport():
    cursor = conn.cursor()
    searchtext = request.form['airportsearchbox']
    #######################################################################
    if len(searchtext)>3:
        error = "Please enter the abbreviation of airport."
        return redirect(url_for('searchpage', error=error))
    #####################################################################
    query = 'select * from flight where (departure_airport = %s or arrival_airport = %s) and (departure_time >= curtime() or arrival_time >= curtime())'
    # query = 'select * from flight where (departure_airport = %s or arrival_airport = %s)'
    cursor.execute(query, (searchtext, searchtext))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if data:
        return render_template('searchFlights.html', results=data)
    else:
        #returns an error message to the html page
        error = 'No results found'
        return redirect(url_for('searchpage', error=error))

@app.route('/searchFlights/date', methods=['POST'])
def searchForDate():
    begintime = request.form['begintime']
    endtime = request.form['endtime']
    
    if not validateDates(begintime, endtime):
        error = 'Invalid date range'
        return redirect(url_for('searchpage', error=error))
    
    cursor = conn.cursor()
    query = 'select * from flight where ((departure_time between %s and %s) or (arrival_time between %s and %s)) and (departure_time >= curtime() or arrival_time >= curtime())'
    # query = 'select * from flight where ((departure_time between %s and %s) or (arrival_time between %s and %s))'
    cursor.execute(query, (begintime, endtime, begintime, endtime))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if data:
        return render_template('searchFlights.html', results=data)
    else:
        #returns an error message to the html page
        error = 'No results found'
        return redirect(url_for('searchpage', error=error))

@app.route('/searchstatus/status', methods=['POST'])
def searchstatus():
    flight_num = request.form['flight number']
    departure_time = request.form['departure_time']
    arrival_time = request.form['arrival_time']
    
    cursor = conn.cursor()
    query = 'select status from flight where flight_num = %s and date(departure_time) = %s and date(arrival_time) = %s'
    cursor.execute(query,(flight_num,departure_time,arrival_time))
    data = cursor.fetchall()
    cursor.close()
    if data:
        return render_template('searchstatus.html', results=data)
    else:
        #returns an error message to the html page
        error = 'No results found'
        return redirect(url_for('searchpage', error=error))
###############################################################################
@app.route('/searchFlights/all', methods=['POST'])
def searchallinfo():
    begintime = request.form['departure_time']
    endtime = request.form['arrival_time']
    dep_airport = request.form['Departure']
    arr_airport = request.form['Arrival']
    dep_city = request.form['dep_city']
    arr_city = request.form['arr_city']

    if not validateDates(begintime, endtime):
        error = 'Invalid date range'
        return redirect(url_for('searchpage', error=error))
    if len(dep_airport)>3 or len(arr_airport)>3:
        error = "Please enter the abbreviation of airport."
        return redirect(url_for('searchpage', error=error))
    cursor = conn.cursor()
    query = 'SELECT * FROM flight, airport, ticket \
          WHERE airport.airport_name=flight.departure_airport \
          AND flight.flight_num = ticket.flight_num AND flight.airline_name = ticket.airline_name\
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
    cursor.execute(query,(dep_city,dep_airport,begintime,endtime,arr_city,arr_airport))
    data = cursor.fetchall()
    cursor.close()
    if data:
        render_template('searchall.html',results = data)
    else:
        #returns an error message to the html page
        error = 'No results found'
        return redirect(url_for('searchpage', error=error))
##################################################################################