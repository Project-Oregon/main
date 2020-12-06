from flask import Flask, render_template, url_for, request, redirect
from db_connector import connect_to_database, execute_query

app = Flask(__name__)

# homepage
@app.route('/')
@app.route('/index.html', methods=['GET'])
def index():
    db_connection = connect_to_database()
    all_locations = 'SELECT * FROM Locations;'
    all_locations_results = execute_query(db_connection,all_locations).fetchall()
    print(f"All Locations in DB: {all_locations_results}")
    return render_template('index.html', index_locations = all_locations_results)

@app.route('/book_ticket.html', methods=['POST', 'GET'])
def book_tickets():
    # GET method used for debugging; prints to terminal pertinent information
    if request.method == 'GET':
        db_connection = connect_to_database()
        cquery = 'SELECT * FROM Customers;'
        cresult = execute_query(db_connection, cquery).fetchall()
        print(f"All Customers in DB: {cresult}")

        pquery = 'SELECT * FROM Transport_Pods;'
        presult = execute_query(db_connection, pquery).fetchall()
        print(f"All Pods in DB: {presult}")

        lquery = 'SELECT locationID, description FROM Locations;'
        lresult = execute_query(db_connection, lquery).fetchall()
        print(f"All Locations in DB: {lresult}")
        return render_template('book_ticket.html', cresults=cresult, presults=presult, lresults=lresult)

    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        partySize = request.form['partySize']
        destination = request.form['destination']

        db_connection = connect_to_database()
        query = "SELECT * FROM Transport_Pods"
        results = execute_query(db_connection, query).fetchall()

        # Looks for first pod that satisfies requirements: operable, fits party size, not in transition, and in Portland
        for result in results:
            if result[1] == True:
                if result[3] > int(partySize):
                    if result[4] == False:
                        if result[5] == 1:
                            currentPod = str(result[0])

                            location_query = "SELECT * FROM Locations"
                            location_results = execute_query(db_connection, location_query).fetchall()
                            for location in location_results:
                                if location[1] == destination:
                                    destination = str(location[0])

                                    customer_query = "INSERT INTO Customers (firstName, lastName, currentPod, destination) VALUES (%s, %s, %s, %s)"
                                    data = (firstName, lastName, currentPod, destination)
                                    execute_query(db_connection, customer_query, data)

                                    update_inTransition = "UPDATE Transport_Pods SET inTransition = True WHERE podID = '%s'" %(currentPod)
                                    execute_query(db_connection, update_inTransition).fetchall()

                                    updated_seats = result[3] - int(partySize)
                                    update_partySize = "UPDATE Transport_Pods SET availableSeat = '%s' WHERE podID = '%s'" %(updated_seats, currentPod)
                                    execute_query(db_connection, update_partySize).fetchall()
                                    
                                    select_inTransition = "SELECT podID FROM Transport_Pods WHERE podID = '%s'" %(currentPod)
                                    select_inTransition_results = execute_query(db_connection, select_inTransition).fetchone()
                                    selectOne = select_inTransition_results[0]

                                    return render_template('ticket_response.html', row=selectOne)

        return render_template('ticket_response_no_pods.html') # no pods available

                                    
@app.route('/customers.html')
def customers():
    db_connection = connect_to_database()
    query = "SELECT customerID, firstName, lastName, currentPod, destination FROM Customers;"
    joint_query = "SELECT customerID, firstName, lastName, currentPod, destination, description FROM Customers INNER JOIN Locations ON Customers.destination = Locations.locationID ORDER BY customerID"
    result = execute_query(db_connection, query).fetchall()
    joint_result = execute_query(db_connection, joint_query).fetchall()
    print(f"All Customers in DB: {result}")
    return render_template('customers.html', rows=joint_result)


@app.route('/engineer_pods.html', methods=['POST', 'GET'])
def engineer_pods():
    if request.method == 'GET':
        db_connection = connect_to_database()
        query = "SELECT engineerID, podID FROM Engineer_Pods;"
        podquery = "SELECT * FROM Transport_Pods;"
        engquery = "SELECT * FROM Service_Engineers;"
        joinquery = "SELECT DISTINCT Engineer_Pods.engineerID, Service_Engineers.firstName, Service_Engineers.lastName, Engineer_Pods.podID FROM Service_Engineers INNER JOIN Engineer_Pods on Service_Engineers.engineerID = Engineer_Pods.engineerID ORDER BY intersectionID"

        result = execute_query(db_connection, query).fetchall()
        print(f"All Engineer_Pods in DB: {result}")        
        podresult = execute_query(db_connection, podquery).fetchall()
        print(f"All Pods in DB: {podresult}")
        engresult = execute_query(db_connection, engquery).fetchall()
        print(f"All Engineers in DB: {engresult}")
        joinresult = execute_query(db_connection,joinquery).fetchall()
        return render_template('engineer_pods.html', rows=result,podresults=podresult, engresults=engresult, joinresults=joinresult)
            
    if request.method == 'POST':
        engineer = request.form['engineerID']
        engID = ""
        i = 0
        while i <len(engineer) and engineer[i]!= ":": # get eng ID from engineer 
            engID += engineer[i]
            i+= 1
        print('eng id', engID)
        podID = request.form['podID']
 
        db_connection = connect_to_database()
        availquery = "SELECT available FROM Service_Engineers WHERE engineerID = %s" %(engID) #ensure engineer is available
        available = execute_query(db_connection, availquery).fetchone()
        
        if available == (1,): 
            dupquery = "SELECT * FROM Engineer_Pods WHERE engineerID = %s AND podID = %s" %(engID, podID)  # ensure won't result in duplicate assignemnt
            duplicate = available = execute_query(db_connection, dupquery).fetchone()

            if duplicate is None:
                print('Creating engineer/pod assignment')
                query = "INSERT INTO Engineer_Pods (engineerID, podID) VALUES (%s, %s)"
                data = engID, podID
                execute_query(db_connection, query, data)
        return redirect(url_for('engineer_pods'))

@app.route('/remove_eng_pod.html', methods=['POST'])
def remove_eng_pod():
    db_connection = connect_to_database()
    engIDpodID = request.form['engineerID_podID']
    engID = ""
    podID = ""
    i = 0
    while i <len(engIDpodID) and engIDpodID[i]!= " ": # get eng ID from engIDpodID
        engID += engIDpodID[i]
        i+= 1
    
    i+=1 
    while i <len(engIDpodID):       # get pod ID from engIDpodID
        podID += engIDpodID[i]
        i+= 1

    if podID == 'None':
        podID = 'NULL'
        query = "DELETE FROM Engineer_Pods WHERE engineerID ="+ engID + " AND podID is "+ podID+";"
    else:
        query = "DELETE FROM Engineer_Pods WHERE engineerID ="+ engID + " AND podID = "+ podID+";"
        
    execute_query(db_connection, query).fetchall()
    print("Successfully removed " + engID + " " + podID )
    
    query = "SELECT engineerID, podID FROM Engineer_Pods;"
    podquery = "SELECT * FROM Transport_Pods;"
    engquery = "SELECT * FROM Service_Engineers;"
    joinquery = "SELECT Engineer_Pods.engineerID, Service_Engineers.firstName, Service_Engineers.lastName, Engineer_Pods.podID FROM Service_Engineers INNER JOIN Engineer_Pods on Service_Engineers.engineerID = Engineer_Pods.engineerID ORDER BY intersectionID"

    result = execute_query(db_connection, query).fetchall()
    print(f"All Engineer_Pods in DB: {result}")        
    podresult = execute_query(db_connection, podquery).fetchall()
    print(f"All Pods in DB: {podresult}")
    engresult = execute_query(db_connection, engquery).fetchall()
    print(f"All Engineers in DB: {engresult}")
    joinresult = execute_query(db_connection,joinquery).fetchall()
    return render_template('engineer_pods.html', rows=result,podresults=podresult, engresults=engresult, joinresults=joinresult)


@app.route('/remove_engineers.html', methods=['POST'])
def removeEngineers():
    engineerID = request.form['engineerID']
    print(engineerID)
    db_connection = connect_to_database()
    query = "DELETE FROM Service_Engineers WHERE engineerID = '%s'" %(engineerID)
    execute_query(db_connection, query).fetchall()
    query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers;"
    result = execute_query(db_connection, query).fetchall()
    print(f"All Engineers in DB: {result}")
    return render_template('engineers.html', rows= result)
        
@app.route('/edit_engineer.html', methods=['POST'])
def edit_engineer():  # submit edits for engineer 
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    engineerID = request.form['engineerID']
    if request.form['available'] == '1':
        available = 'true'
    else:
        available = 'false'
    db_connection = connect_to_database()

    query = "UPDATE Service_Engineers SET firstName = '%s', lastName = '%s', available = %s WHERE engineerID = '%s';" %(firstName, lastName, available, engineerID)
    print(query)
    execute_query(db_connection, query).fetchall()

    query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers;"
    result = execute_query(db_connection, query).fetchall()
    print(f"All Engineers in DB: {result}")
    return render_template('engineers.html', rows= result)

@app.route('/engineers.html', methods=['POST', 'GET'])
def engineers():
    if request.method == 'GET':
        db_connection = connect_to_database()     
        query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers;"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Engineers in DB: {result}")
        return render_template('engineers.html', rows=result)
 
    if request.method == 'POST' and 'engineerID' in request.form:    # populate default data for engineer
        engineerID = request.form['engineerID']
        db_connection = connect_to_database()
        query = "SELECT * FROM Service_Engineers WHERE engineerID = '%s'" %(engineerID)
        print(query)
        eng = execute_query(db_connection, query).fetchall()
        print(eng)
        
        query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers;"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Engineers in DB: {result}")
        return render_template('engineers_edit.html', rows= result, eng=eng)

    if request.method == 'POST' and 'firstName' in request.form:    # add engineer
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        available = request.form['available']
        db_connection = connect_to_database()
        query = "INSERT INTO Service_Engineers (firstName, lastName, available) VALUES (%s, %s, %s)"
        data = firstName, lastName, available
        execute_query(db_connection, query, data)
        return redirect(url_for('engineers'))

    if request.method == 'POST': # search
        lastName = request.form['lastName'] 
        db_connection = connect_to_database()   
        query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers WHERE lastName = '%s'" %(lastName)
        searchresult = execute_query(db_connection, query).fetchall()
        print(f"Search Result: {searchresult}")
        query = "SELECT engineerID, firstName, lastName, available FROM Service_Engineers;"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Engineers in DB: {result}")
        return render_template('engineers.html', searchrows=searchresult, rows= result)
       
    else:
        return render_template('engineers.html')


  
@app.route('/locations.html', methods=['GET', 'POST'])
def locations():
    if request.method == 'GET':
        db_connection = connect_to_database()
        query = "SELECT locationID, description FROM Locations;"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Locations in DB: {result}")
        return render_template('locations.html', rows=result)

    if request.method == 'POST': # add location
        description = request.form['description']

        db_connection = connect_to_database()
        query = "INSERT INTO Locations (description) VALUES (%s)"
        data = (description,)
        execute_query(db_connection, query, data)
        return redirect(url_for('locations'))
       
    else:
        return render_template('locations.html')

@app.route('/removelocations.html', methods=['POST'])
def removeLocations():
    locationID = request.form['locationID']
    db_connection = connect_to_database()
    query = "DELETE FROM Locations WHERE locationID = '%s'" %(locationID)
    execute_query(db_connection, query).fetchall()
    query = "SELECT locationID, description FROM Locations;"
    result = execute_query(db_connection, query).fetchall()
    return render_template('locations.html', rows= result)

@app.route('/removepods.html', methods=['POST'])
def removePods():
    podID = request.form['podID']
    db_connection = connect_to_database()
    query = "DELETE FROM Transport_Pods WHERE podID = '%s'" %(podID)
    execute_query(db_connection, query).fetchall()
    query = "SELECT podID, operableStatus, seatCapacity, availableSeat, inTransition, currentLocation FROM Transport_Pods;"
    result = execute_query(db_connection, query).fetchall()
    return render_template('pods.html', rows= result)

@app.route('/pods.html', methods=['GET', 'POST'])
def pods():
    if request.method == 'GET':
        db_connection = connect_to_database()
        query = "SELECT podID, operableStatus, seatCapacity, availableSeat, inTransition, currentLocation, description FROM Transport_Pods LEFT JOIN Locations ON Transport_Pods.currentLocation = Locations.locationID ORDER BY podID"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Pods in DB: {result}")
        cLoc_query = "SELECT * FROM `Locations`"
        cLoc_result = execute_query(db_connection,cLoc_query).fetchall()
        return render_template('pods.html', rows=result, cloc=cLoc_result)

    # Inserting new pod - automatically set capacity to 5, availableSeat to 5, inTransition status to false
    if request.method == 'POST' and 'operableStatus' in request.form:
        operableStatus = request.form['operableStatus']     #user input
        seatCapacity = '5'
        availableSeat = '5'
        inTransition = '0'
        currentLocation = request.form['currentLocation']   #user input

        db_connection = connect_to_database()
        query = "INSERT INTO Transport_Pods (operableStatus, seatCapacity, availableSeat, inTransition, currentLocation) VALUES (%s, %s, %s, %s, %s)"
        data = operableStatus, seatCapacity, availableSeat, inTransition, currentLocation
        execute_query(db_connection, query, data)
        return redirect(url_for('pods'))

    if request.method == 'POST':    #search
        podID = request.form['podID'] 
        db_connection = connect_to_database()   
        query = "SELECT podID, operableStatus, seatCapacity, availableSeat, inTransition, currentLocation FROM Transport_Pods WHERE podID = '%s'" %(podID)
        searchresult = execute_query(db_connection, query).fetchall()
        print(f"Search Result: {searchresult}")
        query = "SELECT podID, operableStatus, seatCapacity, availableSeat, inTransition, currentLocation FROM Transport_Pods;"
        result = execute_query(db_connection, query).fetchall()
        print(f"All Pods in DB: {result}")
        return render_template('pods.html', searchrows=searchresult, rows= result)
       
    else:
        return render_template('pods.html')

@app.route('/review.html', methods=['GET', 'POST'])
def review():
    if request.method == 'GET':     # populates only pods where inTransition status is True in drop-down menu
        db_connection = connect_to_database()
        podq = "SELECT podID FROM Transport_Pods WHERE inTransition = True"
        podr = execute_query(db_connection,podq).fetchall()        
        return render_template('review.html', podresults=podr)

    if request.method == 'POST':    
        db_connection = connect_to_database()
        podID = request.form['selectedPod']
        techIssue = request.form['techIssue']
        
        # upon submitting a review, pod's inTransition status turns to false
        updateq = "UPDATE Transport_Pods SET inTransition = False WHERE podID = '%s'" %(podID)
        execute_query(db_connection,updateq).fetchall()
        
        # if there is tech issue, update operableStatus to false otherwise stays true
        if techIssue == "Yes":
            inactivatePod = "UPDATE Transport_Pods SET operableStatus = False WHERE podID = '%s'" %(podID)
            execute_query(db_connection,inactivatePod).fetchall()

        # JOIN table to update pod's current location once customer reaches destination
        cust_podq = "SELECT * FROM Customers INNER JOIN Transport_Pods WHERE Customers.currentPod = Transport_Pods.podID AND Transport_Pods.podID = '%s'" %(podID)
        cust_podr = execute_query(db_connection,cust_podq).fetchall()
        for pair in cust_podr:
            customerID = pair[0]
            destination = pair[4]

            updateloc = "UPDATE Transport_Pods SET currentLocation = '%s', availableSeat = 5 WHERE podID = '%s'" %(destination, podID) 
            execute_query(db_connection,updateloc).fetchall()

            deleteC = "DELETE FROM Customers WHERE customerID = '%s'" %(customerID)
            execute_query(db_connection,deleteC).fetchall()
        
        return render_template('index.html')


@app.route('/ticket_response.html')
def ticket_response():
    return render_template('ticket_response.html')    

if __name__ == "__main__":
    app.run(debug=True)
