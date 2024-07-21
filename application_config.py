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
        self.updateDelta()
        self.updateGamma()
        self.updateTheta()
        self.updateVega()
        self.updateRho()
        self.updateVanna()
        self.updateCharm()
        self.updateColour()
        self.updateVomma()
        self.updateZomma()
        self.calculateImpliedVolatility()

    def updateT(self):
        self.t = self.applicationConfig.years_between_dates(self.applicationConfig.currentDateInput, self.expirationDate[0])
    
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
            self.edge = round(self.theoreticalValue - abs(self.premium),10)
        elif 'Short' in self.longShort:
            self.theoreticalValue = -theoreticalValue
            self.edge =  round(abs(self.premium) + self.theoreticalValue,10)

    def calculateDelta(self, S, K, T, r, sigma, option_type, position_type,update: bool):
        if T <= 0:
            if update == True:
                self.delta = 0
            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

        if option_type == 'Call':
            delta = norm.cdf(d1)
        elif option_type == 'Put':
            delta = norm.cdf(d1) - 1
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        

        if position_type == 'Long':
            if update == True:
                self.delta = round(delta,10)
            else:
                return round(delta*100,10)
        elif position_type == 'Short':
            if update == True:
                self.delta = round(-delta,10)
            else:
                return round(-delta*100,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")
    
    def calculateGamma(self,S, K, T, r, sigma, position_type, update: bool):
        if T <= 0:
            if update == True:
                self.gamma = 0
            return None
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        
        if position_type == 'Long':
            if update == True:
                self.gamma = round(gamma,10)
            else:
                return round(gamma*100,10)
        elif position_type == 'Short':
            if update == True:
                self.gamma = round(-gamma,10)
            else:
                return round(-gamma*100,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateVega(self,S, K, T, r, sigma, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.vega = 0
            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        
        vega = S * norm.pdf(d1) * math.sqrt(T)
        
        if position_type == 'Long':
            if update == True:
                self.vega = round(vega/100,10)
            else:
                return round(vega,10)
        elif position_type == 'Short':
            if update == True:
                self.vega = round(-vega/100,10)
            else:
                return round(-vega,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateTheta(self, S, K, T, r, sigma, option_type, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.theta = 0
            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        common_factor = (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
        
        if option_type == 'Call':
            theta = -common_factor - r * K * math.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'Put':
            theta = -common_factor + r * K * math.exp(-r * T) * norm.cdf(-d2)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        

        if position_type == 'Long':
            if update == True:
                self.theta = round(theta/365,10) 
            else:
                return round(theta*100/365,10)
        elif position_type == 'Short':
            if update == True:
                self.theta = round(-theta / 365, 10)
            else:
                return round(-theta*100/365,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.") 

    def calculateRho(self, S, K, T, r, sigma, option_type, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.rho = 0
            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == 'Call':
            rho = K * T * math.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'Put':
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")
        
        if position_type == 'Long':
            if update == True:
                self.rho = round( rho / 100, 10)  
            else:
                return round(rho, 10)
        elif position_type == 'Short':
            if update == True:
                self.rho = round(-rho / 100, 10)
            else:
                return round(-rho, 10)  
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateVanna(self, S, K, T, r, sigma, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.vanna = 0
            return None
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

        vanna = (norm.pdf(d1) * (K - S * math.exp(-r * T))) / (S * sigma)

        if position_type == 'Long':
            if update == True:
                self.vanna = round(vanna,10)
            else:
                return round(vanna *100  ,10)
        elif position_type == 'Short':
            if update == True:
                self.vanna = round(-vanna  ,10)
            else:
                return round(-vanna*100,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateCharm(self, S, K, T, r, sigma, option_type, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.charm = 0

            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if option_type == 'Call':
            charm = -norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * norm.cdf(d1)
        elif option_type == 'Put':
            charm = -norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * norm.cdf(-d1)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

        if position_type == 'Long':
            if update == True:
                self.charm = round(charm / 365,10)
            else:
                return round(charm*100 / 365,10)
        elif position_type == 'Short':
            if update == True:
                self.charm = round(-charm / 365 ,10)
            else:
                return round(-charm*100 / 365 ,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateColour(self, S, K, T, r, sigma, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.colour = 0

            return None

        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

        colour = -gamma * (d1 / (2 * T) + (2 * r * T - d2 * sigma * math.sqrt(T)) / (2 * T * sigma * math.sqrt(T)))

        if position_type == 'Long':
            if update == True:
                self.colour = round(colour / 365  ,10)
            else:
                return round(colour*100 / 365  ,10)
        elif position_type == 'Short':
            if update == True:
                self.colour = round(-colour / 365  ,10)
            else:
                return round(-colour*100 / 365  ,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateVomma(self, S, K, T, r, sigma, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.vomma = 0

            return None
            
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        vega = S * norm.pdf(d1) * math.sqrt(T)

        vomma = vega * d1 * d2 / sigma

        if position_type == 'Long':
            if update == True:
                self.vomma = round( vomma / 100 , 10) 
            else:
                return round( vomma  , 10) 
        elif position_type == 'Short':
            if update == True:
                self.vomma = round( -vomma / 100 , 10)
            else:
                return round( -vomma , 10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def calculateZomma(self, S, K, T, r, sigma, position_type, update:bool):
        if T <= 0:
            if update == True:
                self.zomma = 0
            else:
                return None
            
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

        zomma = gamma * ((d1 * d2 - 1) / sigma)

        if position_type == 'Long':
            if update == True:
                self.zomma = round(zomma,10)
            else:
                return round(zomma*100,10)
        elif position_type == 'Short':
            if update == True:
                self.zomma = round( -zomma,10)
            else:
                return round(-zomma*100,10)
        else:
            raise ValueError("Invalid position type. Use 'long' or 'short'.")

    def updateDelta(self):
        self.calculateDelta(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.optionType[0], self.longShort[0], update=True)

    def updateGamma(self):
        self.calculateGamma(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

    def updateVega(self):
        self.calculateVega(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

    def updateTheta(self):
        self.calculateTheta(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.optionType[0], self.longShort[0], update=True)

    def updateRho(self):
        self.calculateRho(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.optionType[0], self.longShort[0], update=True)

    def updateVanna(self):
        self.calculateVanna(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

    def updateCharm(self):
        self.calculateCharm(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.optionType[0], self.longShort[0], update=True)

    def updateColour(self):
        self.calculateColour(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

    def updateVomma(self):
        self.calculateVomma(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

    def updateZomma(self):
        self.calculateZomma(self.applicationConfig.currentUnderlyingPrice, self.strikePrice[0], self.t, self.applicationConfig.interestRate/100, self.applicationConfig.underlyingVolatility/100, self.longShort[0], update=True)

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
            
            vega_value = self.calculateVega(S, K, T, r, sigma, 'Long', update=False)
            if vega_value == 0:
                self.impliedVolatility ='0%'
                return
            
            sigma -= diff / vega_value

        raise ValueError("Failed to converge to a solution within the maximum number of iterations.")

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
            'edge': round(self.edge*self.quantity[0], 2) if self.t > 0 else 0,
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
        # Position 3 Default - Long butterfly
        self.position3 = [PositionOption(self,'2024-04-01T00:00',90,'Call','Long',1,12),
                          PositionOption(self,'2024-04-01T00:00',100,'Call','Short',2,6),
                          PositionOption(self,'2024-04-01T00:00',110,'Call','Long',1,2)]
        self.p3Totals = []
        self.updatePositionValues()
        self.chart_data = {
            0: self.valuePriceGraph(),
            1: self.greekPriceGraph('Delta'),
            2: self.greekPriceGraph('Gamma'),
            3: self.greekPriceGraph('Vega')
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
        else:
            self.socketio.emit('updateSpecificChart', {'index': index, 'data': self.greekPriceGraph(value)})  
    
    def refreshChart(self, chart):
        if chart == 'Profit/Loss':
            return self.valuePriceGraph()
        else:
            return self.greekPriceGraph(chart)
        
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
    
    def greekPriceGraph(self, greek):
        return {
                'title': greek,
                'xAxisLabel': 'Underlying Price',
                'yAxisLabel': greek,
                'labels': self.generatePriceLabels(),
                'datasets': [
                    {'label': 'Position 1', 'data': self.checkNonZeroList([self.positionGreekPrice('position1', x, greek) for x in self.generatePriceLabels()] if len(self.position1) > 0 else [])},
                    {'label': 'Position 2', 'data': self.checkNonZeroList([self.positionGreekPrice('position2', x, greek) for x in self.generatePriceLabels()] if len(self.position2) > 0 else [])},
                    {'label': 'Position 3', 'data': self.checkNonZeroList([self.positionGreekPrice('position3', x, greek) for x in self.generatePriceLabels()] if len(self.position3) > 0 else [])}
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
    
    def positionGreekPrice(self, position, price, greek):
        positionTotal = 0
        if position == 'position1':
            pos = self.position1
        elif position == 'position2':
            pos = self.position2
        elif position == 'position3':
            pos = self.position3
        for o in pos:
            value = None
            if greek == 'Delta':
                value = self.deltaPrice(o, price)
            elif greek == 'Gamma':
                value =self.gammaPrice(o, price)
            elif greek == 'Vega':
                value = self.vegaPrice(o, price)
            elif greek == 'Theta':
                value = self.thetaPrice(o, price)
            elif greek == 'Rho':
                value = self.rhoPrice(o, price)
            elif greek == 'Vanna':
                value = self.vannaPrice(o, price)
            elif greek == 'Charm':
                value = self.charmPrice(o, price)
            elif greek == 'Colour':
                value = self.colourPrice(o, price)
            elif greek == 'Vomma':
                value = self.vommaPrice(o, price)
            elif greek == 'Zomma':
                value = self.zommaPrice(o, price)

            if value is not None:
                positionTotal += round(value* o.quantity[0],4)
        return positionTotal

    def deltaPrice(self, o, price):
        return o.calculateDelta(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.optionType[0], o.longShort[0], update=False)

    def gammaPrice(self, o, price):
        return o.calculateGamma(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
    
    def vegaPrice(self, o, price):
        return o.calculateVega(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
    
    def thetaPrice(self, o, price):
        return o.calculateTheta(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.optionType[0], o.longShort[0], update=False)
    
    def rhoPrice(self, o, price):
        return o.calculateRho(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.optionType[0], o.longShort[0], update=False)
    
    def vannaPrice(self, o, price):
        return o.calculateVanna(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
    
    def charmPrice(self, o, price):
        return o.calculateCharm(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.optionType[0], o.longShort[0], update=False)
    
    def colourPrice(self, o, price):
        return o.calculateColour(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
    
    def vommaPrice(self, o, price):
        return o.calculateVomma(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
    
    def zommaPrice(self, o, price):
        return o.calculateZomma(price, o.strikePrice[0], o.t, self.interestRate/100, self.underlyingVolatility/100, o.longShort[0], update=False)
        
    def checkNonZeroList(self, lst):
        if list(set(lst)) == [0]:
            return []
        else:
            return lst
    