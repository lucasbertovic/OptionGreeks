import numpy as np
from scipy.stats import norm
from datetime import datetime
from flask_socketio import SocketIO, emit
from datetime import datetime
import math

class PositionOption:
    def __init__(self, applicationConfig, expirationDate, strikePrice, optionType, longShort, quantity, premium):
        self.applicationConfig = applicationConfig
        self.expirationDate = expirationDate,
        self.updateT()
        self.strikePrice = strikePrice, 
        self.optionType = optionType, 
        self.longShort = longShort, 
        self.quantity = quantity,
        self.premium = float(premium) if 'Long' in self.longShort else -float(premium)
        self.updateTheoreticalValue()
        self.totalPremium = self.premium * quantity
        self.updateIntrinsicValue()
        self.delta = None
        self.gamma = None
        self.calculateImpliedVolatility()
        self.updateDelta()
        self.updateGamma()
        self.updateTheta()
        self.updateVega()
        self.updateRho()

    def updateT(self):
        self.t = self.applicationConfig.years_between_dates(self.applicationConfig.currentDateInput, self.expirationDate[0])
    
    def calculateImpliedVolatility(self, tolerance=1e-6, max_iterations=100):
        if self.t <= 0:
            self.impliedVolatility ='0%'
            return
        S = self.applicationConfig.currentUnderlyingPrice
        K = self.strikePrice[0]
        r = self.applicationConfig.interestRate/100
        sigma = self.applicationConfig.underlyingVolatility/100
        T = self.t
        """
        Calculate the implied volatility of a European option using the Newton-Raphson method.
        """
        # Initial guess
        sigma = 0.2
        
        for i in range(max_iterations):
            price = self.applicationConfig.black_scholes(S, K, T, r, sigma, self.optionType[0])
            diff = price - abs(self.premium)
            if abs(diff) < tolerance:
                self.impliedVolatility = str(round(sigma*100,2)) + '%'
                return
            
            vega_value = self.vega(S, K, T, r, sigma)
            if vega_value == 0:
                self.impliedVolatility ='0%'
                return
            
            sigma -= diff / vega_value

        raise ValueError("Failed to converge to a solution within the maximum number of iterations.")
    
    def vega(self, S, K, T, r, sigma):
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        return S * norm.pdf(d1) * math.sqrt(T)

    def updateIntrinsicValue(self):
        self.intrinsicValue = self.applicationConfig.currentUnderlyingPrice - self.strikePrice[0]
        if 'Call' in self.optionType:
            intrinsicValue = max(0, self.applicationConfig.currentUnderlyingPrice - self.strikePrice[0])
        elif 'Put' in self.optionType:
            intrinsicValue = max(0, self.strikePrice[0] - self.applicationConfig.currentUnderlyingPrice)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

        if  'Short' in self.longShort:
            intrinsicValue = -intrinsicValue

        self.intrinsicValue = intrinsicValue

    def updateTheoreticalValue(self):
        theoreticalValue = round(self.applicationConfig.black_scholes(
            self.applicationConfig.currentUnderlyingPrice,
            self.strikePrice[0],
            self.applicationConfig.years_between_dates(self.applicationConfig.currentDateInput, self.expirationDate[0]),
            self.applicationConfig.interestRate / 100,
            self.applicationConfig.underlyingVolatility / 100,
            self.optionType[0]
            ), 2)
        
        if 'Long' in self.longShort:
            self.theoreticalValue = theoreticalValue
            self.edge = round(self.theoreticalValue - abs(self.premium),2)
        elif 'Short' in self.longShort:
            self.theoreticalValue = -theoreticalValue
            self.edge =  round(abs(self.premium) + self.theoreticalValue,2)

    def updateDelta(self):
        if self.t <= 0:
            self.delta = 0
            return
        d1 = (math.log(self.applicationConfig.currentUnderlyingPrice /  self.strikePrice[0]) + ((self.applicationConfig.interestRate/100) + 0.5 * (self.applicationConfig.underlyingVolatility/100)**2) * self.t) / ((self.applicationConfig.underlyingVolatility/100) * math.sqrt(self.t))

        if 'Call' in self.optionType:
            delta = norm.cdf(d1)
        elif 'Put' in self.optionType:
            delta = norm.cdf(d1) - 1
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if  'Short' in self.longShort:
            delta = -delta
        elif  'Long' not in self.longShort:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")
        
        self.delta = round(delta,4)
    
    def updateGamma(self):
        if self.t <= 0:
            self.gamma = 0
            return

        d1 = (math.log(self.applicationConfig.currentUnderlyingPrice /  self.strikePrice[0]) + ((self.applicationConfig.interestRate/100) + 0.5 * (self.applicationConfig.underlyingVolatility/100)**2) * self.t) / ((self.applicationConfig.underlyingVolatility/100) * math.sqrt(self.t))
        pdf_d1 = norm.pdf(d1)
        
        gamma = pdf_d1 / (self.applicationConfig.currentUnderlyingPrice * (self.applicationConfig.underlyingVolatility/100) * math.sqrt(self.t))

        if  'Short' in self.longShort:
            gamma = -gamma
        

        self.gamma = round(gamma,4)

    def updateTheta(self):
        if self.t <= 0:
            self.theta = 0
            return
        S = self.applicationConfig.currentUnderlyingPrice
        K = self.strikePrice[0]
        r = self.applicationConfig.interestRate/100
        sigma = self.applicationConfig.underlyingVolatility/100
        T = self.t
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        

        pdf_d1 = norm.pdf(d1)
        

        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        

        term1 = -(S * pdf_d1 * sigma) / (2 * math.sqrt(T))
        
        if 'Call' in self.optionType:
            term2 = r * K * math.exp(-r * T) * cdf_d2
            theta = term1 - term2
        elif 'Put' in self.optionType:
            term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
            theta = term1 + term2
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if  'Short' in self.longShort:
            theta = -theta
        
        self.theta = round(theta/365,4)

    def updateVega(self):
        if self.t <= 0:
            self.vega = 0
            return
        S = self.applicationConfig.currentUnderlyingPrice
        K = self.strikePrice[0]
        r = self.applicationConfig.interestRate/100
        sigma = self.applicationConfig.underlyingVolatility/100
        T = self.t

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        
        pdf_d1 = norm.pdf(d1)
        
        vega = S * pdf_d1 * math.sqrt(T)
        
        if  'Short' in self.longShort:
            vega = -vega
        
        self.vega = round(vega/100,4)

    def updateRho(self):
        if self.t <= 0:
            self.rho = 0
            return
        S = self.applicationConfig.currentUnderlyingPrice
        K = self.strikePrice[0]
        r = self.applicationConfig.interestRate/100
        sigma = self.applicationConfig.underlyingVolatility/100
        T = self.t
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        cdf_d2 = norm.cdf(d2)
        cdf_neg_d2 = norm.cdf(-d2)
        

        if 'Call' in self.optionType:
            rho = K * T * math.exp(-r * T) * cdf_d2
        elif 'Put' in self.optionType:
            rho = -K * T * math.exp(-r * T) * cdf_neg_d2
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if  'Short' in self.longShort:
            rho = -rho
        
        self.rho = round(rho/100,4)
    
    def to_dict(self):
        return {
            'exercise_price': self.strikePrice,
            'type': self.optionType,
            'position': self.longShort,
            'expirationDate': self.expirationDate,
            'impliedVolatility': self.impliedVolatility,
            'price_unit': self.premium,
            'quantity': self.quantity,
            'total_price': self.totalPremium,
            'theoreticalValue': round(float(self.theoreticalValue[0])*self.quantity[0],2) if isinstance(self.theoreticalValue, tuple) else round(float(self.theoreticalValue)*self.quantity[0],2) ,
            'edge': round(self.edge*self.quantity[0], 4) if self.t > 0 else 0,
            'delta': round(self.delta*self.quantity[0], 4),
            'gamma': round(self.gamma*self.quantity[0], 4),
            'theta': round(self.theta*self.quantity[0], 4),
            'vega': round(self.vega*self.quantity[0], 4),
            'rho': round(self.rho*self.quantity[0], 4),
        }

class ApplicationConfig:
    def __init__(self, socketio):
        self.socketio = socketio
        self.currentView = 'greeks'
        self.transactionPrice = None
        self._currentUnderlyingPrice = 100
        self._underlyingVolatility = 25
        self._currentDateInput = '2024-01-01T00:00'
        self._interestRate = 6
        self._expirationDateTime = '2024-04-01T00:00'
        self._optionType = 'Call'
        self._longShort = 'Long'
        self._quantity = 1
        self._strikePrice = 100
        self.update_theoretical_value()
        # Position 1 Default - Short Condor
        self.position1 = [PositionOption(self,'2024-04-01T00:00',90,'Call','Short',1,12.38),
                          PositionOption(self,'2024-04-01T00:00',95,'Call','Long',1,8.68),
                          PositionOption(self,'2024-04-01T00:00',105,'Call','Long',1,3.52),
                          PositionOption(self,'2024-04-01T00:00',110,'Call','Short',1,2.04)]
        self.p1Totals = []
        # Position 2 Default - Put ratio spread (sell more than buy)
        self.position2 = [PositionOption(self,'2024-04-01T00:00',100,'Put','Long',1,4),
                          PositionOption(self,'2024-04-01T00:00',90,'Put','Short',2,2)]
        self.p2Totals = []
        # Position 3 Default - Long Call Christmas Tree 
        self.position3 = [PositionOption(self,'2024-04-01T00:00',90,'Call','Long',1,12),
                          PositionOption(self,'2024-04-01T00:00',100,'Call','Short',2,6),
                          PositionOption(self,'2024-04-01T00:00',110,'Call','Long',1,2)]
        self.p3Totals = []
        self.updatePositionValues()
        self.chart_data = {
            0: self.valuePriceGraph(),
            1: self.deltaPriceGraph(),
            2: self.gammaPriceGraph(),
            3: self.vegaPriceGraph()
        }
        self._chart1 = 'Profit/Loss'
        self._chart2 = 'Delta'
        self._chart3 = 'Gamma'
        self._chart4 = 'Vega'
    
    @property
    def currentUnderlyingPrice(self):
        return self._currentUnderlyingPrice

    @currentUnderlyingPrice.setter
    def currentUnderlyingPrice(self, value):
        self._currentUnderlyingPrice = value
        self.update_theoretical_value()
        self.updatePositionValues()
        self.updateChartData()
        
    @property
    def underlyingVolatility(self):
        return self._underlyingVolatility

    @underlyingVolatility.setter
    def underlyingVolatility(self, value):
        self._underlyingVolatility = value
        self.update_theoretical_value()
        self.updatePositionValues()
        self.updateChartData()

    @property
    def currentDateInput(self):
        return self._currentDateInput

    @currentDateInput.setter
    def currentDateInput(self, value):
        self._currentDateInput = value
        for o in self.position1:
            o.updateT()
        for o in self.position2:
            o.updateT()
        for o in self.position3:
            o.updateT()
        self.update_theoretical_value()
        self.updatePositionValues()
        self.updateChartData()
        
    @property
    def interestRate(self):
        return self._interestRate

    @interestRate.setter
    def interestRate(self, value):
        self._interestRate = value
        self.update_theoretical_value()
        self.updatePositionValues()
        self.updateChartData()

    @property
    def expirationDateTime(self):
        return self._expirationDateTime

    @expirationDateTime.setter
    def expirationDateTime(self, value):
        self._expirationDateTime = value
        self.update_theoretical_value()

    @property
    def optionType(self):
        return self._optionType

    @optionType.setter
    def optionType(self, value):
        self._optionType = value
        self.update_theoretical_value()

    @property
    def longShort(self):
        return self._longShort

    @longShort.setter
    def longShort(self, value):
        self._longShort = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = value

    @property
    def strikePrice(self):
        return self._strikePrice

    @strikePrice.setter
    def strikePrice(self, value):
        self._strikePrice = value
        self.update_theoretical_value()

    @property
    def chart1(self):
        return self._chart1

    @chart1.setter
    def chart1(self, value):
        self._chart1 = value
        index = 0
        self.updateSpecificChart(index, value)

    @property
    def chart2(self):
        return self._chart2

    @chart2.setter
    def chart2(self, value):
        self._chart2 = value
        index = 1
        self.updateSpecificChart(index, value)

    @property
    def chart3(self):
        return self._chart3

    @chart3.setter
    def chart3(self, value):
        self._chart3 = value
        index =2
        self.updateSpecificChart(index, value) 

    @property
    def chart4(self):
        return self._chart4

    @chart4.setter
    def chart4(self, value):
        self._chart4 = value
        index = 3
        self.updateSpecificChart(index, value)

    def update_theoretical_value(self):
        self.theoreticalValue = round(self.black_scholes(
            self.currentUnderlyingPrice,
            self.strikePrice,
            self.years_between_dates(self.currentDateInput, self.expirationDateTime),
            self.interestRate / 100,
            self.underlyingVolatility / 100,
            self.optionType
        ), 2)
        
        self.socketio.emit('update_theoretical_value', {'theoreticalValue': self.theoreticalValue})
    
    def black_scholes(self, S, K, T, r, sigma, option_type):
        if T < 0:
            return 0
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == 'Call':
            price = (S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
        elif option_type == 'Put':
            price = (K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))
        else:
            raise ValueError("Invalid option type. Use 'Call' or 'Put'.")
        return price

    def years_between_dates(self, date_str1, date_str2):
        dt1 = datetime.strptime(date_str1, "%Y-%m-%dT%H:%M")
        dt2 = datetime.strptime(date_str2, "%Y-%m-%dT%H:%M")
        delta = dt2 - dt1
        years = delta.total_seconds() / (365.25 * 24 * 3600)
        return round(years, 10)
    
    def convert_datetime_format(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        formatted_date = dt.strftime("%d/%m/%y %I:%M%p").lower()
        return formatted_date
    
    def updatePositionValues(self):
        for o in self.position1:
            o.updateIntrinsicValue()
            o.updateDelta()
            o.updateTheoreticalValue()
            o.updateGamma()
            o.updateTheta()
            o.updateVega()
            o.updateRho()
        for o in self.position2:
            o.updateIntrinsicValue()
            o.updateDelta()
            o.updateTheoreticalValue()
            o.updateGamma()
            o.updateTheta()
            o.updateVega()
            o.updateRho()
        for o in self.position3:
            o.updateIntrinsicValue()
            o.updateDelta()
            o.updateTheoreticalValue()
            o.updateGamma()
            o.updateTheta()
            o.updateVega()
            o.updateRho()
        table_data = {
            'position1': [obj.to_dict() for obj in self.position1],
            'position2': [obj.to_dict() for obj in self.position2],
            'position3': [obj.to_dict() for obj in self.position3]
        }
        self.updatePositionTotals()
        self.socketio.emit('update_table', table_data)


    def updatePositionTotals(self):
        if len(self.position1) > 0:
            p1Elements = [[o.quantity[0]
                            ,round(o.premium*o.quantity[0],2)
                            ,round(o.theoreticalValue*o.quantity[0],2)
                            ,round(o.edge*o.quantity[0],2) if o.t > 0 else 0
                            , round(o.delta*o.quantity[0],4)
                            , round(o.gamma*o.quantity[0],4)
                            , round(o.theta*o.quantity[0],4)
                            , round(o.vega*o.quantity[0],4)
                            , round(o.rho*o.quantity[0],4)] for o in self.position1]
            p1Array = np.array(p1Elements)
            p1Totals = list(np.sum(p1Array, axis=0))
            p1Totals = [round(e,4) for e in p1Totals]
            self.socketio.emit('updateP1Totals', p1Totals)
        else:
            self.socketio.emit('updateP1Totals', ['-','-','-','-','-','-','-','-','-'])
        if len(self.position2) > 0:
            p2Elements = [[o.quantity[0]
                            ,round(o.premium*o.quantity[0],2)
                            ,round(o.theoreticalValue*o.quantity[0],2)
                            ,round(o.edge*o.quantity[0],2)
                            , round(o.delta*o.quantity[0],4)
                            , round(o.gamma*o.quantity[0],4)
                            , round(o.theta*o.quantity[0],4)
                            , round(o.vega*o.quantity[0],4)
                            , round(o.rho*o.quantity[0],4)] for o in self.position2]
            p2Array = np.array(p2Elements)
            p2Totals = list(np.sum(p2Array, axis=0))
            p2Totals = [round(e,4) for e in p2Totals]
            self.socketio.emit('updateP2Totals', p2Totals)
        else:
            self.socketio.emit('updateP2Totals', ['-','-','-','-','-','-','-','-','-'])
        if len(self.position3) > 0:
            p3Elements = [[o.quantity[0]
                            ,round(o.premium*o.quantity[0],2)
                            ,round(o.theoreticalValue*o.quantity[0],2)
                            ,round(o.edge*o.quantity[0],2)
                            , round(o.delta*o.quantity[0],4)
                            , round(o.gamma*o.quantity[0],4)
                            , round(o.theta*o.quantity[0],4)
                            , round(o.vega*o.quantity[0],4)
                            , round(o.rho*o.quantity[0],4)] for o in self.position3]
            p3Array = np.array(p3Elements)
            p3Totals = list(np.sum(p3Array, axis=0))
            p3Totals = [round(e,4) for e in p3Totals]
            self.socketio.emit('updateP3Totals', p3Totals)
        else:
            self.socketio.emit('updateP3Totals', ['-','-','-','-','-','-','-','-','-'])
    
    def updateSpecificChart(self, index, value):
        if value == 'Profit/Loss':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.valuePriceGraph()})
        elif value == 'Delta':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.deltaPriceGraph()})
        elif value == 'Gamma':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.gammaPriceGraph()})
        elif value == 'Vega':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.vegaPriceGraph()})
        elif value == 'Theta':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.thetaPriceGraph()})
        elif value == 'Rho':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.rhoPriceGraph()})
        elif value == 'Vanna':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.vannaPriceGraph()})
        elif value == 'Charm':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.charmPriceGraph()})
        elif value == 'Colour':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.colourPriceGraph()})
        elif value == 'Vomma':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.vommaPriceGraph()})
        elif value == 'Zomma':
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.zommaPriceGraph()})
    
    def refreshChart(self, chart):
        if chart == 'Profit/Loss':
            return self.valuePriceGraph()
        elif chart == 'Delta':
            return self.deltaPriceGraph()
        elif chart == 'Gamma':
            return self.gammaPriceGraph()
        elif chart == 'Vega':
            return self.vegaPriceGraph()
        elif chart == 'Theta':
            return self.thetaPriceGraph()
        elif chart == 'Rho':
            return self.rhoPriceGraph()
        elif chart == 'Vanna':
            return self.vannaPriceGraph()
        elif chart == 'Charm':
            return self.charmPriceGraph()
        elif chart == 'Colour':
            return self.colourPriceGraph()
        elif chart == 'Vomma':
            return self.vommaPriceGraph()
        elif chart == 'Zomma':
            return self.zommaPriceGraph()
        
    def updateChartData(self):
        self.chart_data = {
            0: self.refreshChart(self.chart1),
            1: self.refreshChart(self.chart2),
            2: self.refreshChart(self.chart3),
            3: self.refreshChart(self.chart4)
        }
        for index, data in self.chart_data.items():
            self.socketio.emit('update_chart', {'index': index, 'labels': data['labels'], 'datasets': data['datasets']})

    def valuePriceGraph(self):
        return {
                'title': 'Profit/Loss',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Profit/Loss',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionValuePrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionValuePrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionValuePrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def deltaPriceGraph(self):
        return {
                'title': 'Delta',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Delta',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionDeltaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionDeltaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionDeltaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def gammaPriceGraph(self):
        return {
                'title': 'Gamma',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Gamma',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionGammaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionGammaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionGammaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def vegaPriceGraph(self):
        return {
                'title': 'Vega',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Vega',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionVegaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionVegaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionVegaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def thetaPriceGraph(self):
        return {
                'title': 'Theta',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Theta',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionThetaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionThetaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionThetaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def rhoPriceGraph(self):
        return {
                'title': 'Rho',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Rho',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionRhoPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionRhoPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionRhoPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def vannaPriceGraph(self):
        return {
                'title': 'Vanna',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Vanna',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionVannaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionVannaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionVannaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def charmPriceGraph(self):
        return {
                'title': 'Charm',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Charm',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionCharmPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionCharmPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionCharmPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def colourPriceGraph(self):
        return {
                'title': 'Colour',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Colour',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionColourPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionColourPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionColourPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def vommaPriceGraph(self):
        return {
                'title': 'Vomma',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Vomma',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionVommaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionVommaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionVommaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }
    
    def zommaPriceGraph(self):
        return {
                'title': 'Zomma',
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': 'Zomma',
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionZommaPrice('position1', x) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionZommaPrice('position2', x) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionZommaPrice('position3', x) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
                ]
            }

    def generatePriceLabels(self):
        return [i for i in range(50,151)]

    def positionValuePrice(self,position, price):
        positionEdge = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            if o.t < 0:
                continue
            else:
                value = round(self.black_scholes(
                    price,
                    o.strikePrice[0],
                    self.years_between_dates(self.currentDateInput, o.expirationDate[0]),
                    self.interestRate / 100,
                    self.underlyingVolatility / 100,
                    o.optionType[0]
                    ), 2)
                
                if 'Long' in o.longShort:
                    theoreticalValue = value
                    edge = round(theoreticalValue - abs(o.premium),2)
                elif 'Short' in o.longShort:
                    theoreticalValue = -value
                    edge =  round(abs(o.premium) + theoreticalValue,2)
                
                positionEdge += edge * o.quantity[0]
        return positionEdge
    
    def positionDeltaPrice(self,position, price):
        positionDelta = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            delta = self.deltaPrice(o, price)
            if delta is not None:
                positionDelta += round(delta * o.quantity[0],4)
        return positionDelta
    
    def positionGammaPrice(self,position, price):
        positionGamma = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            gamma = self.gammaPrice(o, price)
            if gamma is not None:
                positionGamma += round(gamma * o.quantity[0],4)
        return positionGamma
    
    def positionVegaPrice(self,position, price):
        positionVega = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            vega = self.vegaPrice(o, price)
            if vega is not None:
                positionVega += round(vega * o.quantity[0],4)
        return positionVega

    def positionThetaPrice(self,position, price):
        positionTheta = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            theta = self.thetaPrice(o, price)
            if theta is not None:
                positionTheta += round(theta * o.quantity[0],4)
        return positionTheta
    
    def positionRhoPrice(self,position, price):
        positionRho = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            rho = self.rhoPrice(o, price)
            if rho is not None:
                positionRho += round(rho * o.quantity[0],4)
        return positionRho

    def positionVannaPrice(self,position, price):
        positionVanna = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            vanna = self.vannaPrice(o, price)
            if vanna is not None:
                positionVanna += round(vanna * o.quantity[0],4)
        return positionVanna
    
    def positionCharmPrice(self,position, price):
        positionCharm = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            charm = self.charmPrice(o, price)
            if charm is not None:
                positionCharm += round(charm * o.quantity[0],4)
        return positionCharm
    
    def positionColourPrice(self,position, price):
        positionColour = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            colour = self.colourPrice(o, price)
            if colour is not None:
                positionColour += round(colour * o.quantity[0],4)
        return positionColour
    
    def positionVommaPrice(self,position, price):
        positionVomma = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            vomma = self.vommaPrice(o, price)
            if vomma is not None:
                positionVomma += round(vomma * o.quantity[0],4)
        return positionVomma
    
    def positionZommaPrice(self,position, price):
        positionZomma = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            zomma = self.zommaPrice(o, price)
            if zomma is not None:
                positionZomma += round(zomma * o.quantity[0],4)
        return positionZomma

    def deltaPrice(self, o, price):
        try:
            d1 = (math.log(price /  o.strikePrice[0]) + ((self.interestRate/100) + 0.5 * (self.underlyingVolatility/100)**2) * o.t) / ((self.underlyingVolatility/100) * math.sqrt(o.t))
        except:
            return None
        if 'Call' in o.optionType:
            delta = norm.cdf(d1)
        elif 'Put' in o.optionType:
            delta = norm.cdf(d1) - 1
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if  'Short' in o.longShort:
            delta = -delta
        elif  'Long' not in o.longShort:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")
        return round(delta*100,4)
    
    def gammaPrice(self, o, price):
        try:
            d1 = (math.log(price /  o.strikePrice[0]) + ((self.interestRate/100) + 0.5 * (self.underlyingVolatility/100)**2) * o.t) / ((self.underlyingVolatility/100) * math.sqrt(o.t))
        except:
            return None
        pdf_d1 = norm.pdf(d1)
        
        gamma = pdf_d1 / (self.currentUnderlyingPrice * (self.underlyingVolatility/100) * math.sqrt(o.t))
        
        if  'Short' in o.longShort:
            gamma = -gamma
        

        return round(gamma*100,4)
    
    def vegaPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        pdf_d1 = norm.pdf(d1)
        

        vega = S * pdf_d1 * math.sqrt(T)

        if  'Short' in o.longShort:
            vega = -vega
        
        return round(vega,4)
    
    def thetaPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
        
        if 'Call' in o.optionType:
            theta = (-S * sigma * norm.pdf(d1) / (2 * math.sqrt(T)) -
                    r * K * math.exp(-r * T) * norm.cdf(d2))
        elif 'Put' in o.optionType:
            theta = (-S * sigma * norm.pdf(d1) / (2 * math.sqrt(T)) +
                    r * K * math.exp(-r * T) * norm.cdf(-d2))
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

        if  'Short' in o.longShort:
            theta = -theta
        
        theta_per_day = theta / 365.0
        return round(theta_per_day*100,4)
    
    def rhoPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
        
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d2 = norm.cdf(-d2)
        

        if 'Call' in o.optionType:
            rho = K * T * math.exp(-r * T) * cdf_d2
        elif 'Put' in o.optionType:
            rho = -K * T * math.exp(-r * T) * cdf_neg_d2
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if  'Short' in o.longShort:
            rho = -rho
        
        return round(rho,4)
    
    def vannaPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
    
        vanna = (S * norm.pdf(d1) * (1 - d1 / sigma)) / sigma
        
        if  'Short' in o.longShort:
            vanna = -vanna
        
        return round(vanna,4)
    
    def charmPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
    
        if 'Call' in o.optionType:
            charm = (norm.pdf(d1) * ((r - 0.5 * sigma ** 2) / (sigma * math.sqrt(T)) - d2 / (2 * T))) - r * norm.cdf(d1)
        elif 'Put' in o.optionType:
            charm = (norm.pdf(d1) * ((r - 0.5 * sigma ** 2) / (sigma * math.sqrt(T)) - d2 / (2 * T))) + r * norm.cdf(-d1)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

        if  'Short' in o.longShort:
            charm = -charm

        charm_per_day = charm / 365.0
        return round(charm_per_day*100,4)
    
    def colourPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
        part1 = -norm.pdf(d1) / (2 * S * T * sigma * math.sqrt(T))
        part2 = (2 * r * T - d2 * sigma * math.sqrt(T)) / (sigma * math.sqrt(T))
        color = part1 * part2
        
        if  'Short' in o.longShort:
            color = -color

        color_per_day = color / 365.0
        return round(color_per_day*100,4)
    
    def vommaPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
        vomma = S * norm.pdf(d1) * math.sqrt(T) * d1 * d2 / sigma

        if  'Short' in o.longShort:
            vomma = -vomma
        
        return round(vomma,2)
    
    def zommaPrice(self, o, price):
        S = price
        K = o.strikePrice[0]
        r = self.interestRate/100
        sigma = self.underlyingVolatility/100
        T = o.t
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        except:
            return None
        d2 = d1 - sigma * math.sqrt(T)
        zomma = (norm.pdf(d1) * (d1 * d2 - 1)) / (S ** 2 * sigma ** 2 * T)

        if  'Short' in o.longShort:
            zomma = -zomma
        
        return round(zomma*100,4)
        
    def checkNonZeroList(self, lst):
        if list(set(lst)) == [0]:
            return []
        else:
            return lst
    