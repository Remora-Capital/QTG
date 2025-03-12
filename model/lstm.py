import numpy as np
import pandas as pd
import yfinance as yf

data = yf.download("AMZN", start="2006-01-01", end="2018-01-01")
data.columns = data.columns.droplevel(1)
data.reset_index(inplace=True)
data.head()


price = data[['Close']]
price.info()

from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(-1, 1))
price['Close'] = scaler.fit_transform(price['Close'].values.reshape(-1,1))


def split_data(stock, lookback):
    data_raw = stock.to_numpy() # convert to numpy array
    data = []
    
    # create all possible sequences of length seq_len
    for index in range(len(data_raw) - lookback): 
        data.append(data_raw[index: index + lookback])
    
    data = np.array(data);
    test_set_size = int(np.round(0.2*data.shape[0]));
    train_set_size = data.shape[0] - (test_set_size);
    
    x_train = data[:train_set_size,:-1,:]
    y_train = data[:train_set_size,-1,:]
    
    x_test = data[train_set_size:,:-1]
    y_test = data[train_set_size:,-1,:]
    
    return [x_train, y_train, x_test, y_test]


lookback = 20 # choose sequence length
x_train, y_train, x_test, y_test = split_data(price, lookback)
print('x_train.shape = ',x_train.shape)
print('y_train.shape = ',y_train.shape)
print('x_test.shape = ',x_test.shape)
print('y_test.shape = ',y_test.shape)


import torch
import torch.nn as nn

x_train = torch.from_numpy(x_train).type(torch.Tensor)
x_test = torch.from_numpy(x_test).type(torch.Tensor)
y_train = torch.from_numpy(y_train).type(torch.Tensor)
y_test = torch.from_numpy(y_test).type(torch.Tensor)



from torch.utils.data import Dataset, DataLoader

class MyDataset(Dataset):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __getitem__(self, index):
        return self.x[index], self.y[index]
    
    def __len__(self):
        return len(self.x)
    



train_data = MyDataset(x_train, y_train)
test_data = MyDataset(x_test, y_test)

batch_size = 16
train_loader = DataLoader(dataset=train_data, batch_size=batch_size, shuffle=True, num_workers=0)
test_loader = DataLoader(dataset=test_data, batch_size=batch_size, shuffle=False, num_workers=0)



input_dim = 1
hidden_dim = 32
num_layers = 2
output_dim = 1
num_epochs = 100



class LSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super(LSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        out = self.fc(out[:, -1, :]) 
        return out
    


model = LSTM(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim, num_layers=num_layers)
criterion = torch.nn.MSELoss(reduction='mean')
optimiser = torch.optim.Adam(model.parameters(), lr=0.01)


train_losses = np.zeros(num_epochs)
test_losses = np.zeros(num_epochs)

for epoch in range(num_epochs):
    epoch_loss = 0
    total_samples = 0


    model.train()
    for idx, (x, y) in enumerate(train_loader):
        optimiser.zero_grad()

        outputs = model(x) # (batch_size, 1)
        loss = criterion(outputs, y) # (batch_size, 1)

        loss.backward()
        optimiser.step()

        epoch_loss += loss.item()
        total_samples += x.size(0)
    
    print(f'Epoch {epoch} Train Loss: {epoch_loss / total_samples}')
    train_losses[epoch] = epoch_loss / total_samples

outs = np.empty(0)
model.eval()
for idx, (x, y) in enumerate(train_loader):
    outputs = model(x)
    outs = np.append(outs, outputs.detach().numpy())

outs


# import time

# hist = np.zeros(num_epochs)
# start_time = time.time()
# lstm = []

# for t in range(num_epochs):
#     y_train_pred = model(x_train)

#     loss = criterion(y_train_pred, y_train)
#     print("Epoch ", t, "MSE: ", loss.item())
#     hist[t] = loss.item()

#     optimiser.zero_grad()
#     loss.backward()
#     optimiser.step()
    
# training_time = time.time()-start_time
# print("Training time: {}".format(training_time))

# predict = pd.DataFrame(scaler.inverse_transform(y_train_pred.detach().numpy()))
# original = pd.DataFrame(scaler.inverse_transform(y_train.detach().numpy()))


predict = pd.DataFrame(scaler.inverse_transform(outs.reshape(-1,1)))
original = pd.DataFrame(scaler.inverse_transform(y_train.detach().numpy()))

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("darkgrid")    

fig = plt.figure()
fig.subplots_adjust(hspace=0.2, wspace=0.2)

plt.subplot(1, 2, 1)
ax = sns.lineplot(x = original.index, y = original[0], label="Data", color='royalblue')
ax = sns.lineplot(x = predict.index, y = predict[0], label="Training Prediction (LSTM)", color='tomato')
ax.set_title('Stock price', size = 14, fontweight='bold')
ax.set_xlabel("Days", size = 14)
ax.set_ylabel("Cost (USD)", size = 14)
ax.set_xticklabels('', size=10)


plt.subplot(1, 2, 2)
ax = sns.lineplot(data=train_losses, color='royalblue')
ax = sns.lineplot(data=test_losses, color='tomato')
ax.set_xlabel("Epoch", size = 14)
ax.set_ylabel("Loss", size = 14)
ax.set_title("Training Loss", size = 14, fontweight='bold')
fig.set_figheight(6)
fig.set_figwidth(16)