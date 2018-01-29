# Dyna-Q
import os
import sys
import random
import numpy as np
import common_functions as common
random.seed(1)

'''
Action: a in {buy: 1, hold: 0, sell: -1}
State : (risk, stock) risk, stock in INT: risk = p_stdev, stock = number of stock
'''
class ReinforcementLearning:
    ''' Constructor'''
    def __init__(self, train_data, test_data):
        self._close = train_data
        self._pred = test_data
        self._portfolios = {date: 0 for date in (list(self._close.keys())+list(self._pred.keys()))}
        self._alp = 0.2     # Learning rate
        self._gam = 0.6     # Discount rate
        self._span = 21     # Spans for standerd devision
        self._div = 1     # State divide 状態の分割単位：標準偏差の0.5倍分割
        self._myu = 1.5     # リスク調整係数
        ''' Init'''
        self._states = {0: (0, 0)}
        self._q = {0: {1: 0, 0: 0, -1: 0}}       # Q-Table
        self._model = {0: {
                         1: {'reward': 0, 'state': 0},
                         0: {'reward': 0, 'state': 0},
                        -1: {'reward': 0, 'state': 0},
                      }}

    def _eps_greedy(self, state_id):
        state = self._states[state_id]
        while True:
            action = random.choice([-1, 0, 1])
            if random.random() > 0.001:
                action = max(self._q[state_id], key=self._q[state_id].get)
            if not (state[1] == 0 and action == -1):
                break
        return action

    def _get_start_pos(self, date_list, date):
        for idx in range(len(date_list)):
            if date_list[idx] == date:
                pos = idx
                break
        return pos

    def _exprimental(self, date, state_id, action):
        reward, state = 0, self._states[state_id]
        stock = state[1]
        date_list = list(self._close.keys())
        pos_today = self._get_start_pos(date_list, date)
        pre_date = date_list[pos_today-1]
        if action == 1:
            ''' buy'''
            stock += 1
        elif action == -1:
            ''' sell'''
            reward += self._close[date]
            stock -= 1
        else:
            ''' hold'''
            reward = 0
        self._portfolios[date] += self._portfolios[pre_date]+reward
        prev_20 = np.array([self._portfolios[key] for key in list(self._close.keys())[pos_today-self._span: pos_today-1]])
        std = np.std(prev_20)
        if std == 0:
            risk = 0
        else:
            risk = int(self._portfolios[date]/(self._div*self._myu*std))
        next_state = (risk, stock)
        idx = len(self._states)
        if next_state not in self._states.values():
            self._states[idx] = next_state
        else:
            for i, s in self._states.items():
                if s == next_state: idx = i
        return reward, idx

    def _is_exist_state(self, state_id):
        if state_id not in self._q:
            self._q[state_id] = {1: 0, 0: 0, -1: 0}
            self._model[state_id] = {
                                     1: {'reward': 0, 'state': 0},
                                     0: {'reward': 0, 'state': 0},
                                    -1: {'reward': 0, 'state': 0},
                                 }

    def training(self):
        for i in range(100):
            current = 0
            ''' Episorde start '''
            for date in list(self._close.keys())[self._span:-1]:
                self._is_exist_state(current)
                action = self._eps_greedy(current)
                reward, next_state = self._exprimental(date, current, action)
                self._is_exist_state(next_state)
                ''' Direct ReinforcementLearning '''
                max_q = max(self._q[next_state].values())
                self._q[current][action] += self._alp*(reward+self._gam*max_q-self._q[current][action])
                ''' Update Model '''
                self._model[current][action] = {'reward': reward, 'state': next_state}
                ''' Plannning '''
                s_list = [s_id for s_id in self._states.keys() if self._states[s_id][1] <= self._states[current][1]+1 and self._states[s_id][1] >= self._states[current][1]-1]
                for j in range(500):
                    state = random.choice(s_list)
                    action = random.choice([-1, 0, 1])
                    reward, tmp_next_state = self._model[state][action]['reward'], self._model[state][action]['state']
                    max_q = max(self._q[tmp_next_state].values())
                    self._q[state][action] += self._alp*(reward+self._gam*max_q-self._q[state][action])
                current = next_state
            print('episorde: %d, Q-table size: %d'%(i, len(self._q)))
            for key in self._q.keys(): print('%d: %s'%(key, str(self._q[key])))
            #for key in self._states.keys(): print('%d: %s'%(key, str(self._states[key])))

    def predict(self):
        train_list = list(self._close.keys())
        date_list = list(self._pred.keys())
        stock = 0
        for date in date_list[:-1]:
            d_list = train_list + date_list
            pos_today = self._get_start_pos(d_list, date)
            pre_date = d_list[pos_today-1]
            prev_20 = np.array([self._portfolios[key] for key in d_list[pos_today-self._span: pos_today-1]])
            std = np.std(prev_20) # 標準偏差の算出
            if std == 0:
                risk = 0
            else:
                risk = int(self._portfolios[pre_date]/(self._div*self._myu*std))
            next_state = (risk, stock)
            state_id = 0
            for i, s in self._states.items():
                if s == next_state: state_id = i
            action = 0
            print(next_state)
            if state_id in self._q:
                action = max(self._q[state_id], key=self._q[state_id].get)
            stock += action
            print('%s: action: %d: %s'%(date, action, self._q[state_id]))
            self._portfolios[date] = self._portfolios[pre_date]+action*self._pred[date]

if __name__=='__main__':
    train_data = common.readClose('7203', 0, 320)
    pred_data = common.readClose('7203', 320, 360)
    rl = ReinforcementLearning(train_data, pred_data)
    rl.training()
    rl.predict()
