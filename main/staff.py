from flask import Flask, render_template, request, session, redirect, url_for
import pymysql.cursors
import datetime
from pyecharts import options as opts
from pyecharts.charts import Pie,Bar

from appdef import *

#Get the airline the staff member works for
def getStaffAirline():
    username = session['username']
    cursor = conn.cursor()
    #username is a primary key
    query = 'select airline_name from airline_staff where username = %s'
    cursor.execute(query, (username))
    #fetchall returns an array, each element is a dictionary
    airline = cursor.fetchall()[0]['airline_name']
    cursor.close()
    
    return airline

#Make sure that the user is actually staff before performing any operations
def authenticateStaff():
    username = ""
    try:
        #could be that there is no user, make sure
        username = session['username']
    except:
        return False
    
    cursor = conn.cursor()
    query = 'select * from airline_staff where username=%s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if data:
        return True
    else:
        #Logout before returning error message
        session.pop('username')
        return False

@app.route('/staffHome')
def staffHome():
    if authenticateStaff():
        username = session['username']
        message = request.args.get('message')
        cursor = conn.cursor()

        queryGetairline = "SELECT airline_name FROM airline_staff WHERE username= %s"
        cursor.execute(queryGetairline, username)
        airline_name = cursor.fetchone()['airline_name']
        # query top destination for the past 3 months
        query1 = "select count(ticket.ticket_id) as cnt, airport.airport_city as city\
                from airport,flight,ticket,purchases\
                where airport.airport_name = flight.arrival_airport\
                and flight.flight_num = ticket.flight_num\
                and flight.airline_name = %s\
                and purchases.ticket_id = ticket.ticket_id\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 3 MONTH) and curdate()\
                group by city \
                order by cnt DESC limit 3"
        cursor.execute(query1,airline_name)
        data1 = cursor.fetchall()
        if len(data1)<3:
            num = len(data1)
            range1 = range(num)
            data1 = [data1[i]['city'] for i in range(num)]
        else:
            range1 = range(3)
            data1 = [data1[i]['city'] for i in range(3)]

        # query top destination for the past 1 year
        query2 = "select count(ticket.ticket_id) as cnt, airport.airport_city as city\
                from airport,flight,ticket,purchases\
                where airport.airport_name = flight.arrival_airport\
                and flight.flight_num = ticket.flight_num\
                and flight.airline_name = %s\
                and purchases.ticket_id = ticket.ticket_id\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 1 YEAR) and curdate()\
                group by city \
                order by cnt DESC limit 3"
        cursor.execute(query2,airline_name)
        data2 = cursor.fetchall()
        if len(data2)<3:
            num = len(data2)
            range2 = range(num)
            data2 = [data2[i]['city'] for i in range(num)]
        else:
            range2 = range(3)
            data2 = [data2[i]['city'] for i in range(3)]
        cursor.close()
        
        return render_template('staff.html', username=username,
                                            message=message,
                                            destination1 = data1,
                                            destination2 = data2,
                                            range1 = range1,
                                            range2 = range2)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights')
def searchFlightsPage():
    if authenticateStaff():
        cursor = conn.cursor()
        
        airline = getStaffAirline()
        
        query = "select * from flight where airline_name = %s \
                and ((departure_time between curdate() and date_add(curdate(), interval 30 day)) \
                or (arrival_time between curdate() and date_add(curdate(), interval 30 day)))"
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        
        cursor.close()
        
        error = request.args.get('error')
        return render_template('searchStaff.html', error=error, results=data)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/searchFlights/city', methods=['POST'])
def searchFlightsCity():
    if authenticateStaff():
        cursor = conn.cursor()
        city = request.form['citysearchbox']
        airline = getStaffAirline()
        query = "select * from flight,airport \
        where (airport.airport_name=flight.departure_airport or airport.airport_name=flight.arrival_airport) \
        and airport.airport_city=%s and airline_name=%s"
        cursor.execute(query, (city, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/searchFlights/airport', methods=['POST'])
def searchFlightsAirport():
    if authenticateStaff():
        cursor = conn.cursor()
        airport = request.form['airportsearchbox']
        airline = getStaffAirline()
        query = 'select * from flight where (departure_airport = %s or arrival_airport = %s) and airline_name=%s'
        cursor.execute(query, (airport, airport, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights/date', methods=['POST'])
def searchFlightsDate():
    if authenticateStaff():
        begintime = request.form['begintime']
        endtime = request.form['endtime']
        
        if not validateDates(begintime, endtime):
            error = 'Invalid date range'
            return redirect(url_for('searchFlightsPage', error=error))
        
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = "select * from flight \
        where ((departure_time between %s and %s) \
        or (arrival_time between %s and %s)) and airline_name=%s"
        cursor.execute(query, (begintime, endtime, begintime, endtime, airline))
        data = cursor.fetchall()
        cursor.close()
        error = None
        if data:
            return render_template('searchStaffResults.html', results=data)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/searchFlights/customers', methods=['POST'])
def searchFlightsCustomer():
    if authenticateStaff():
        flightnum = request.form['flightsearchbox']
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = "select customer_email from purchases natural join ticket\
         where flight_num = %s and airline_name=%s"
        cursor.execute(query, (flightnum, airline))
        data = cursor.fetchall()
        cursor.close()
        if data:
            return render_template('searchStaffResults.html', customerresults=data, flightnum=flightnum)
        else:
            #returns an error message to the html page
            error = 'No results found'
            return redirect(url_for('searchFlightsPage', error=error))
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/createFlight')
def createFlightPage():
    if authenticateStaff():
        airline = getStaffAirline()
        cursor = conn.cursor()
        airline = getStaffAirline()
        
        query = "select * from flight where airline_name = %s \
                and ((departure_time between curdate() and date_add(curdate(), interval 30 day)) \
                or (arrival_time between curdate() and date_add(curdate(), interval 30 day)))"
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        
        cursor = conn.cursor()
        query = 'select distinct airport_name from airport'
        cursor.execute(query)
        airportdata = cursor.fetchall()
        
        query = 'select distinct airplane_id from airplane where airline_name=%s'
        cursor.execute(query, (airline))
        airplanedata = cursor.fetchall()
        
        cursor.close()
        
        error = request.args.get('error')
        return render_template('createFlight.html', error = error, 
                                                    airportdata = airportdata,
                                                    airplanedata = airplanedata,
                                                    results = data)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/createFlight/Auth', methods=['POST'])
def createFlight():
    # prevent unauthorized users from doing this action
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    flightnum = request.form['flightnum']
    departport = request.form['departport']
    departtime = request.form['departtime']
    arriveport = request.form['arriveport']
    arrivetime = request.form['arrivetime']
    price = request.form['price']
    status = "Upcoming"
    airplaneid = request.form['airplanenum']
    ##########################################################################
    airline = getStaffAirline()

    cursor = conn.cursor()
    query1 = 'select * from flight where airline_name = %s and flight_num = %s'
    cursor.execute(query1,(airline,flightnum))
    data1 = cursor.fetchall()

    if data1:
        error = "The flight number already exists, please enter another one."
        return redirect(url_for('createFlightPage', error=error))
    cursor.close()
#############################################################################
#############################################################################
    cursor = conn.cursor()
    query2 = 'select * from airport where airport_name = %s '
    cursor.execute(query2,(departport))
    data2 = cursor.fetchall()
    query3 = 'select * from airport where airport_name = %s '
    cursor.execute(query3,(arriveport))
    data3 = cursor.fetchall()

    if (not data2):
        error = "The Departure Airport does not exist, please add the airport first."
        return redirect(url_for('createFlightPage', error=error))
    if (not data3):
        error = "The Arrival Airport does not exist, please add the airport first."
        return redirect(url_for('createFlightPage', error=error))

    cursor.close()
#############################################################################
    
    if not validateDates(departtime, arrivetime):
            error = 'Invalid date range'
            return redirect(url_for('createFlightPage', error=error))
    
    airline = getStaffAirline()
    
    #Check that airplane is valid
    cursor = conn.cursor()
    query = 'select * from airplane where airplane_id = %s'
    cursor.execute(query, (airplaneid))
    data = cursor.fetchall()
    if not data:
        error = 'Invalid Airplane ID'
        return redirect(url_for('createFlightPage', error=error))
    
    query = 'insert into flight values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(query, (airline, flightnum, departport, departtime, arriveport, arrivetime, price, status, airplaneid))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))

@app.route('/staffHome/changeFlight')
def changeFlightStatusPage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('changeFlight.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/changeFlight/Auth', methods=['POST'])
def changeFlightStatus():
    # prevent unauthorized users from doing this action
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    cursor = conn.cursor()
    flightnum = request.form['flightnum']
    status = request.form['status']
    if not status:
        error = 'Did not select new status'
        return redirect(url_for('changeFlightStatusPage', error=error))
    
    airline = getStaffAirline()
    
    #Check that the flight is from the same airline as the staff
    query = 'select * from flight where flight_num = %s and airline_name = %s'
    cursor.execute(query, (flightnum, airline))
    data = cursor.fetchall()
    ##################################################################################
    if not data:
        error = 'Incorrect enter - flight number is not in your airline '
        return redirect(url_for('changeFlightStatusPage', error=error))
    ##################################################################################
    
    #Update the specified flight
    query = 'update flight set status=%s where flight_num=%s and airline_name = %s'
    cursor.execute(query, (status, flightnum, airline))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))
    
@app.route('/staffHome/addAirplane')
def addAirplanePage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('addAirplane.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/addAirplane/confirm', methods=['POST'])
def addAirplane():
    # prevent unauthorized users from doing this action
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    planeid = request.form['id']
    seats = request.form['seats']
    airline = getStaffAirline()
    
    #Check if planeid is not taken
    cursor = conn.cursor()
    query = 'select * from airplane where airplane_id = %s'
    cursor.execute(query, (planeid))
    data = cursor.fetchall()
    
    if data:
        error = "Airplane ID already taken"
        return redirect(url_for('addAirplanePage', error=error))
    
    #Insert the airplane
    query = 'insert into airplane values (%s, %s, %s)'
    cursor.execute(query, (airline, planeid, seats))
    conn.commit()
    
    #Get a full list of airplanes
    query = 'select * from airplane where airline_name = %s'
    cursor.execute(query, (airline))
    data = cursor.fetchall()
    cursor.close()
    
    return render_template('addAirplaneConfirm.html', results=data)

@app.route('/staffHome/addAirport')
def addAirportPage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('addAirport.html', error=error)
    else:
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/addAirport/Auth', methods=['POST'])
def addAirport():
    # prevent unauthorized users from doing this action
    if not authenticateStaff():
        error = 'Invalid Credentials'
        return redirect(url_for('errorpage', error=error))
    
    username = session['username']
    
    name = request.form['name']
    city = request.form['city']
    #####################################################################
    if len(name)>3:
        error = "Please enter the abbreviation of airport."
        return redirect(url_for('addAirportPage', error=error))
    cursor = conn.cursor()
    query = "select * from airport where airport_name = %s and airport_city = %s"
    cursor.execute(query,(name,city))
    data1 = cursor.fetchall()
    cursor.close()
    if data1:
        error = "Airport Already exits."
        return redirect(url_for('addAirportPage', error=error))
    #####################################################################
    
    cursor = conn.cursor()
    query = 'insert into airport values (%s, %s)'
    cursor.execute(query, (name, city))
    conn.commit()
    cursor.close()
    
    return redirect(url_for('staffHome', message="Operation Successful"))

@app.route('/staffHome/viewAgents')
def viewAgentsPage():
    if authenticateStaff():
        error = request.args.get('error')
        return render_template('viewAgents.html', error=error)
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/viewAgents/sales', methods=['POST'])
def viewAgentsSales():
    if authenticateStaff():
        daterange = request.form['range']
        airline = getStaffAirline()
        
        #datrange specify the past 1 month or year
        cursor = conn.cursor()
        query = 'select email,count(ticket_id) as sales \
        from booking_agent natural join purchases natural join ticket \
        where purchase_date >= date_sub(curdate(), interval 1 ' + daterange + ') \
        and airline_name=%s group by email order by sales DESC limit 5'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        
        #Use only the top 5 sellers
        #Python will not break if we try to access a range that extends beyond the end of the array
        return render_template('viewAgentsSales.html', results = data[0:5], date=daterange)
        
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/viewAgents/commission')
def viewAgentsCommission():
    if authenticateStaff():
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = "select email,sum(flight.price)*0.1 as commission \
        from booking_agent natural join purchases natural join ticket natural join flight \
        where purchase_date >= date_sub(curdate(), interval 1 year) and airline_name=%s\
         group by email order by commission DESC limit 5"
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        
        #Use only the top 5 sellers
        #Python will not break if we try to access a range that extends beyond the end of the array
        return render_template('viewAgentsCommission.html', results = data[0:5])
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/viewCustomers')
def viewCustomersPage():
    if authenticateStaff():
        airline = getStaffAirline()
        
        cursor = conn.cursor()
        query = 'select customer_email, count(ticket_id) as customerpurchases \
                from purchases natural join ticket \
                where airline_name= %s \
                and purchase_date >= date_sub(curdate(), interval 1 year) group by customer_email \
                having customerpurchases \
                  >= all (select count(ticket_id) \
                  from purchases natural join ticket \
                  where airline_name = %s \
                  and purchase_date >= date_sub(curdate(), interval 1 year) GROUP by customer_email)'
        cursor.execute(query, (airline, airline))
        data = cursor.fetchall()
        cursor.close()
        
        error = request.args.get('error')
        return render_template('viewCustomers.html', error=error, results=data)
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))

@app.route('/staffHome/viewCustomers/results', methods=['POST'])
def viewCustomers():
    if authenticateStaff():
        airline = getStaffAirline()
        customer = request.form['email']
        
        cursor = conn.cursor()
        query1 = "select * from customer where email = %s"
        cursor.execute(query1,customer)
        data1 = cursor.fetchone()
        error = request.args.get('error')
        cursor.close()

        if not data1:
            error = "Not a customer email, please enter a customer email."
            return redirect(url_for('viewCustomersPage',error = error))
        else:
            cursor = conn.cursor()
            query = 'select distinct flight_num from purchases natural join ticket where airline_name = %s and customer_email=%s'
            cursor.execute(query, (airline, customer))
            data = cursor.fetchall()
            cursor.close()
            
            return render_template('viewCustomersResults.html', results=data, customer=customer)
        
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))
    
@app.route('/staffHome/viewReports')
def viewReportsPage():
    if authenticateStaff():
        airline = getStaffAirline()
        currentmonth = datetime.datetime.now().month
        monthtickets = []
        
        cursor = conn.cursor()
        for i in range(0, 12):
            query = 'select count(ticket_id) as sales \
            from purchases natural join ticket \
            where year(purchase_date) = year(curdate() - interval ' + str(i) + ' month) \
            and month(purchase_date) = month(curdate() - interval ' + str(i) + ' month) \
            and airline_name=%s'
            cursor.execute(query, (airline))
            data = cursor.fetchall()
            salemonth = ((currentmonth - (i+1)) % 12) + 1
            # print (data[0]['sales'])
            monthtickets.append([data[0]['sales'], salemonth])
        
        cursor.close()
        c1 = (
                Bar()
                .add_xaxis([d[1] for d in monthtickets])
                .add_yaxis('total ticket number',[d[0] for d in monthtickets])
                .set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0)),
                          title_opts=opts.TitleOpts(title="Ticket Amount in the Past",
                          subtitle= "In the past 1 year"),
                          legend_opts=opts.LegendOpts(pos_right="15%"))
            )
        error = request.args.get('error')
        return render_template('viewReports.html', 
                                bar_options1=c1.dump_options(),error = error)
    else:
        error = "Invalid Credentials"
        return redirect(url_for('errorpage', error=error))
        
@app.route('/staffHome/viewReports/dates', methods=['POST'])
def viewReportsDates():
    if authenticateStaff():
        airline = getStaffAirline()
        begintime = request.form['begintime']
        endtime = request.form['endtime']
        
        if not validateDates(begintime, endtime):
            error = 'Invalid date range'
            return redirect(url_for('viewReportsPage', error=error))
        
        cursor = conn.cursor()
        query = 'select count(ticket_id) as sales \
                from purchases natural join ticket where airline_name=%s\
                and purchase_date between %s and %s'
        cursor.execute(query, (airline, begintime, endtime))
        data = cursor.fetchall()
        cursor.close()
        
        return render_template('viewReportsDate.html', sales=data[0]['sales'], begintime=begintime, endtime=endtime)
    else:
        error = "Invalid Credentials"
        return render_template('error.html',error=error)
    
@app.route('/staffHome/viewReports/past', methods=['POST'])
def viewReportsPast():
    if authenticateStaff():
        airline = getStaffAirline()
        daterange = request.form['range']
        
        cursor = conn.cursor()
        query = 'select count(ticket_id) as sales \
        from purchases natural join ticket where airline_name=%s \
        and purchase_date >= date_sub(curdate(), interval 1 ' + daterange + ')'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        
        return render_template('viewReportsPast.html', sales=data[0]['sales'], datetime=daterange)
    else:
        error = "Invalid Credentials"
        return render_template('error.html',error=error)

@app.route('/staffHome/ComparisonRevenue')
def ComparisonRevenue():
    if authenticateStaff():
        username = session['username']
        error = None
        # query for airline_name the staff works for
        cursor = conn.cursor()
        queryGetairline = "SELECT airline_name FROM airline_staff WHERE username= %s"
        cursor.execute(queryGetairline, username)
        airline_name = cursor.fetchone()['airline_name']
        # query for direct purchase revenue (last month)
        query1 = "select sum(flight.price) as rev\
                from purchases, ticket, flight\
                where purchases.ticket_id = ticket.ticket_id \
                and ticket.flight_num = flight.flight_num\
                and ticket.airline_name = flight.airline_name\
                and flight.airline_name = %s\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 1 MONTH) and curdate()\
                and purchases.booking_agent_id is null"
        cursor.execute(query1,str(airline_name))
        direct_revenue = cursor.fetchone()['rev']
        # query for indirect purchase revenue (last month)
        query2 = "select sum(flight.price) as rev\
                from purchases, ticket, flight\
                where purchases.ticket_id = ticket.ticket_id \
                and ticket.flight_num = flight.flight_num\
                and ticket.airline_name = flight.airline_name\
                and flight.airline_name = %s\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 1 MONTH) and curdate()\
                and purchases.booking_agent_id is not null"
        cursor.execute(query2,str(airline_name))
        indirect_revenue = cursor.fetchone()['rev']

        #draw the pie chart (last month)

        x_data = ['Direct Revenue','Indirect Revenue']
        y_data = [direct_revenue,indirect_revenue]
        data_pair = [list(z) for z in zip(x_data, y_data)]

        c1 = (
            Pie()
            .add('',[d for d in data_pair])
            .set_global_opts(title_opts=opts.TitleOpts(title="Revenue Comparison",
                                                    subtitle = "Last Month"),
                            legend_opts=opts.LegendOpts(pos_right="15%"))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )

        #Customized pie (a fancier version pie chart)

        # c1 = (
        #     Pie()
        #     .add(
        #     series_name="Revenue Source",
        #     data_pair=data_pair,
        #     rosetype="radius",
        #     radius="55%",
        #     center=["50%", "50%"],
        #     label_opts=opts.LabelOpts(is_show=False, position="center"),
        # )
        # .set_global_opts(
        #     title_opts=opts.TitleOpts(
        #         title="Revenue Source (last month)",
        #         pos_left="center",
        #         pos_top="20",
        #         title_textstyle_opts=opts.TextStyleOpts(color="black"),
        #     ),
        #     legend_opts=opts.LegendOpts(is_show=False),
        # )
        # .set_series_opts(
        #     tooltip_opts=opts.TooltipOpts(
        #         trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        #     ),
        #     label_opts=opts.LabelOpts(color="rgba(0,0,0,255)"),
        # )
        # )

        # query for direct purchase revenue (last year)
        query1_ = "select sum(flight.price) as rev\
                from purchases, ticket, flight\
                where purchases.ticket_id = ticket.ticket_id \
                and ticket.flight_num = flight.flight_num\
                and ticket.airline_name = flight.airline_name\
                and flight.airline_name = %s\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 1 YEAR) and curdate()\
                and purchases.booking_agent_id is null"
        cursor.execute(query1_,str(airline_name))
        direct_revenue_ = cursor.fetchone()['rev']
        # query for indirect purchase revenue (last month)
        query2_ = "select sum(flight.price) as rev\
                from purchases, ticket, flight\
                where purchases.ticket_id = ticket.ticket_id \
                and ticket.flight_num = flight.flight_num\
                and ticket.airline_name = flight.airline_name\
                and flight.airline_name = %s\
                and purchases.purchase_date between DATE_SUB(curdate(), INTERVAL 1 YEAR) and curdate()\
                and purchases.booking_agent_id is not null"
        cursor.execute(query2_,str(airline_name))
        indirect_revenue_ = cursor.fetchone()['rev']
        cursor.close()

        #draw the pie chart (last month)

        x_data_ = ['Direct Revenue','Indirect Revenue']
        y_data_ = [direct_revenue_,indirect_revenue_]
        data_pair_ = [list(z) for z in zip(x_data_, y_data_)]

        c2 = (
            Pie()
            .add('',[d for d in data_pair_])
            .set_global_opts(title_opts=opts.TitleOpts(title="Revenue Comparison",
                                                    subtitle = "Last Year"),
                            legend_opts=opts.LegendOpts(pos_right="15%"))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )


        if direct_revenue and indirect_revenue:
            return render_template('ComparisonRevenue.html',
                                pie_options1 = c1.dump_options(),
                                pie_options2 = c2.dump_options())
        else:
            error = 'Sorry! No data available Right Now.'
            return render_template('ComparisonRevenue.html',error = error)
    else:
        error = "Invalid Credentials"
        return render_template('error.html',error=error)
