from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from application_config import ApplicationConfig, PositionOption
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
config = ApplicationConfig(socketio)

initial_values = {
    'currentUnderlyingPrice': 100,
    'underlyingVolatility': 25,
    'currentDateInput': '2024-01-01T00:00',
    'interestRate': 6,
    'expirationDateTime': '2024-04-01T00:00',
    'optionType': 'Call',
    'longShort': 'Long',
    'quantity': 1,
    'strikePrice': 100,
}

@app.route('/')
def home():
    # Reset to initial values
    config.currentView = 'greeks'
    config.transactionPrice = None
    config.currentUnderlyingPrice = initial_values['currentUnderlyingPrice']
    config.underlyingVolatility = initial_values['underlyingVolatility']
    config.currentDateInput = initial_values['currentDateInput']
    config.interestRate = initial_values['interestRate']
    config.expirationDateTime = initial_values['expirationDateTime']
    config.optionType = initial_values['optionType']
    config.longShort = initial_values['longShort']
    config.quantity = initial_values['quantity']
    config.strikePrice = initial_values['strikePrice']
    config.update_theoretical_value()
    # Position 1 Default - Short Condor
    config.position1 = [PositionOption(config,'2024-04-01T00:00',90,'Call','Short',1,12.38),
                        PositionOption(config,'2024-04-01T00:00',95,'Call','Long',1,8.68),
                        PositionOption(config,'2024-04-01T00:00',105,'Call','Long',1,3.52),
                        PositionOption(config,'2024-04-01T00:00',110,'Call','Short',1,2.04)]
    config.p1Totals = []
    # Position 2 Default - Put ratio spread (sell more than buy)
    config.position2 = [PositionOption(config,'2024-04-01T00:00',100,'Put','Long',1,4),
                        PositionOption(config,'2024-04-01T00:00',90,'Put','Short',2,2)]
    config.p2Totals = []
    # Position 3 Default - Long Butterfly
    config.position3 = [PositionOption(config,'2024-04-01T00:00',90,'Call','Long',1,12),
                        PositionOption(config,'2024-04-01T00:00',100,'Call','Short',2,6),
                        PositionOption(config,'2024-04-01T00:00',110,'Call','Long',1,2)]
    config.p3Totals = []
    config.updatePositionValues()
    config.chart_data = {
        0: config.valuePriceGraph(),
        1: config.greekPriceGraph('Delta'),
        2: config.greekPriceGraph('Gamma'),
        3: config.greekPriceGraph('Vega')
    }
    config.chart1 = 'Profit/Loss'
    config.chart2 = 'Delta'
    config.chart3 = 'Gamma'
    config.chart4 = 'Vega'
    return render_template('index.html', 
                           currentUnderlyingPrice=config.currentUnderlyingPrice,
                           underlyingVolatility=config.underlyingVolatility,
                           currentDateInput=config.currentDateInput,
                           interestRate=config.interestRate,
                           expirationDateTime=config.expirationDateTime,
                           optionType=config.optionType,
                           longShort=config.longShort,
                           quantity=config.quantity,
                           strikePrice=config.strikePrice,
                           theoreticalValue=config.theoreticalValue)

@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.get_json()
    if config.currentUnderlyingPrice != float(data['currentUnderlyingPrice']):
        config.currentUnderlyingPrice = float(data['currentUnderlyingPrice'])
    if config.underlyingVolatility != float(data['underlyingVolatility']):
        config.underlyingVolatility = float(data['underlyingVolatility'])
    if config.currentDateInput != data['currentDateInput']:
        config.currentDateInput = data['currentDateInput']
    if config.interestRate != float(data['interestRate']):
        config.interestRate = float(data['interestRate'])
    socketio.emit('update_theoretical_value', {'theoreticalValue': config.theoreticalValue})
    return jsonify({'message': 'Data updated successfully'})

@app.route('/update_position_inputter', methods=['POST'])
def update_position_inputter():
    data = request.get_json()
    config.expirationDateTime = data['expirationDateTime']
    config.optionType = data['optionType']
    config.longShort = data['longShort']
    config.quantity = int(data['quantity'])
    config.strikePrice = int(data['strikePrice'])
    try:
        config.transactionPrice = int(data['transactionPrice'])
    except:
        config.transactionPrice = data['transactionPrice'] 
    socketio.emit('update_theoretical_value', {'theoreticalValue': config.theoreticalValue})
    return jsonify({'message': 'Data updated successfully'})

@app.route('/chart_data', methods=['GET'])
def get_chart_data():
    config.updatePositionValues()
    index = request.args.get('index', type=int, default=0)
    data = config.chart_data.get(index, {'title': 'No data available', 'labels': [], 'datasets': [], 'xAxisLabel': '', 'yAxisLabel': ''})
    return jsonify(data)

@app.route('/update_option', methods=['POST'])
def update_option():
    new_option = PositionOption(
        config,
        config.expirationDateTime,
        config.strikePrice,
        config.optionType,
        config.longShort,
        config.quantity,
        config.transactionPrice
    )

    if config.currentView == 'position1':
        config.position1.append(new_option)
        config.updatePositionTotals()
        
    elif config.currentView == 'position2':
        config.position2.append(new_option)
        config.updatePositionTotals()
        
    elif config.currentView == 'position3':
        config.position3.append(new_option)
        config.updatePositionTotals()
    return jsonify({"message": "Option updated successfully"})

@app.route('/clear_position', methods=['POST'])
def clear_position():
    if config.currentView == 'position1':
        config.position1 = []
    elif config.currentView == 'position2':
        config.position2 = []
    elif config.currentView == 'position3':
        config.position3 = []
    config.updatePositionTotals()
    config.updateChartData()
    return jsonify({'status': 'success', 'message': 'Position cleared'}), 200

@app.route('/get_table_data', methods=['GET'])
def get_table_data():
    if config.currentView == 'position1':
        table_data = [config.position1[-1].to_dict()]
    elif config.currentView == 'position2':
        table_data = [config.position2[-1].to_dict()]
    elif config.currentView == 'position3':
        table_data = [config.position3[-1].to_dict()]
    return jsonify(table_data)

@socketio.on('button_clicked')
def handle_button_click(data):
    current_view = data['view']
    if config.currentView == 'greeks':
        table_data = {
            'position1': [obj.to_dict() for obj in config.position1],
            'position2': [obj.to_dict() for obj in config.position2],
            'position3': [obj.to_dict() for obj in config.position3]
        }
        config.updatePositionTotals()
        config.socketio.emit('update_table', table_data)
    if current_view == 'greeks':
        config.updateChartData()
    config.currentView = data['view']

@socketio.on('changeGraphFromDropdown')
def handle_button_click(data):
    if data['dropdownId'] == 'dropdown1':
        config.chart1 = data['value']
    if data['dropdownId'] == 'dropdown2':
        config.chart2 = data['value']
    if data['dropdownId'] == 'dropdown3':
        config.chart3 = data['value']
    if data['dropdownId'] == 'dropdown4':
        config.chart4 = data['value']

if __name__ == '__main__':
    socketio.run(app, debug=True)
