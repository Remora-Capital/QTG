import numpy as np
import torch
import torch.nn as nn
import yfinance as yf
from tqdm.notebook import tqdm
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score

# hyperparameters
train_test_prop = 0.8
batch_size = 16
block_size = 8 # the temporal block size of the model
epochs = 100
learning_rate = 0.01
device = 'cuda' if torch.cuda.is_available() else 'cpu'
show_stats = True

# model parameters
n_hidden = 128
n_layer = 2
dropout = 0.2

torch.manual_seed(1337)

data = yf.download("AMZN")
data.columns = data.columns.droplevel(1)
# data = data["2020-01-01":]

data["1D Return"] = data["Close"].pct_change(1)
data["5D Return"] = data["Close"].pct_change(5)
data["20D Return"] = data["Close"].pct_change(20)
data["80D Return"] = data["Close"].pct_change(80)
data["120D Return"] = data["Close"].pct_change(120)
data["160D Return"] = data["Close"].pct_change(160)
data["200D Return"] = data["Close"].pct_change(200)
data["20D EMA"] = data["Close"].ewm(span=20, adjust=False).mean()
data["80D EMA"] = data["Close"].ewm(span=80, adjust=False).mean()
data["120D EMA"] = data["Close"].ewm(span=120, adjust=False).mean()
data["160D EMA"] = data["Close"].ewm(span=160, adjust=False).mean()
data["200D EMA"] = data["Close"].ewm(span=200, adjust=False).mean()
data.dropna(inplace=True)

data.drop(columns=["Adj Close", "Open", "High", "Low", "Volume"], inplace=True)
data

split_index = int(data.shape[0] * train_test_prop)
train_x = data.iloc[:split_index]
test_x = data.iloc[split_index:]
train_y = train_x["Close"].shift(-1).dropna()
test_y = test_x["Close"].shift(-1).dropna()
train_x = train_x.loc[train_y.index]
test_x = test_x.loc[test_y.index]
assert train_x.index.equals(train_y.index)
assert test_x.index.equals(test_y.index)

train_x.shape, train_y.shape, test_x.shape, test_y.shape

scaler = StandardScaler()
scaler.fit(train_x)
train_x = scaler.transform(train_x)
test_x = scaler.transform(test_x)
# train_x = train_x.to_numpy()
# test_x = test_x.to_numpy()


class TimeSeriesDataset(Dataset):
    def __init__(self, x, y, block_size):
        self.x = x
        self.y = y
        self.block_size = block_size

    def __len__(self):
        return len(self.y) - self.block_size + 1

    def __getitem__(self, idx):
        if idx + self.block_size > len(self.x):
            raise IndexError("Index out of bounds")
        return (
            torch.tensor(self.x[idx:idx+self.block_size], dtype=torch.float32),
            torch.tensor(self.y[idx+self.block_size-1], dtype=torch.float32).unsqueeze(-1)
        )
    
train_dataset = TimeSeriesDataset(train_x, train_y.to_numpy(), block_size)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

test_dataset = TimeSeriesDataset(test_x, test_y.to_numpy(), block_size)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout):
        super(LSTMModel, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x: (batch_size, block_size, feature_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).requires_grad_().to(device)

        # Initialize cell state
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).requires_grad_().to(device)

        # We need to detach as we are doing truncated backpropagation through time (BPTT)
        # If we don't, we'll backprop all the way to the start even after going through another batch
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        
        # out: (batch_size, block_size, hidden_size), contains all hidden states in block_size. We only want the last one.
        out = self.fc(out[:, -1, :]) 

        # out: (batch_size, 1)
        return out
    

model = LSTMModel(input_size=train_x.shape[1], hidden_size=n_hidden, num_layers=n_layer, dropout=dropout)
model.to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)


def run_epoch(model, criterion, loader, optimizer, is_train):
    if is_train:
        model.train()
    else:
        model.eval()
    
    epoch_loss = 0
    total_samples = 0

    for x, y in loader:
        if is_train:
            optimizer.zero_grad()
        
        x = x.to(device)
        y = y.to(device)
        
        batchsize = x.shape[0]
                            
        out = model(x)
        loss = criterion(out, y)

        if is_train:
            loss.backward()
            optimizer.step()

        epoch_loss += loss.item() * batchsize
        total_samples += batchsize
        #potential idea: only get validation loss every x epochs?
    
    return epoch_loss / total_samples


train_losses = np.zeros(epochs)
test_losses = np.zeros(epochs)

for epoch in tqdm(range(epochs)):
    train_loss = run_epoch(model, criterion, train_loader, optimizer, is_train=True)
    test_loss = run_epoch(model, criterion, test_loader, optimizer, is_train=False)
    train_losses[epoch] = train_loss
    test_losses[epoch] = test_loss

    if show_stats:
        tqdm.write(f"\rEpoch[{epoch+1}/{epochs}] | loss train: {train_loss}, test: {test_loss}", end="\r")


plt.plot(train_losses, label='train')

plt.plot(test_losses, label='test')

plt.legend()

plt.show()



model.eval()

predicted_train = np.array([])

for idx, (x, y) in enumerate(train_loader):
    # print(scaler.inverse_transform(x.cpu()), y) TODO: CHECK WHAT THIS IS PREDICTING!
    x = x.to(device)
    out = model(x)
    out = out.cpu().detach().numpy()
    predicted_train = np.concatenate((predicted_train, out.squeeze(-1)))


to_plot_data_y_train_pred = np.zeros(len(data))

to_plot_data_y_train_pred[:split_index-block_size] = predicted_train

to_plot_data_y_train_pred = np.where(to_plot_data_y_train_pred == 0, None, to_plot_data_y_train_pred)



dates = data.index


fig = plt.figure(figsize=(25, 5), dpi=80)
fig.patch.set_facecolor((1.0, 1.0, 1.0))
plt.plot(dates, data["Close"], label="Actual close", color="blue")
plt.plot(dates, to_plot_data_y_train_pred, label="Predicted close (train)", color="red")
plt.title("Compare predicted close to actual close")
# plt.grid(b=None, which='major', axis='y', linestyle='--')
plt.legend()
plt.show()