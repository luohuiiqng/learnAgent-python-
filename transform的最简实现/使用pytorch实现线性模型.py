import torch

#1.数据准备(Prepare dataset)
#2.设计模型(Design model using class)
#3.构造损失和优化器(Co nstruct loss and optimizer)
#4.训练的周期(Training cycle)

#数据准备
 x_data = torch.Tensor([[1.0],[2.0],[3.0]])
 y_data = torch.Tensor([[2.0],[4.0],[6.0]])

 #设计模型
 class LinearModel(torch.nn.Module):
    def __init__(self):
        super(LinearModel,self).__init__()
        self.linera = torch.nn.Linear(1,1)


    def forward(self,x):
        y_pred = self.linera(x)
        return y_pred

model = LinearModel()


#狗仔损失函数和优化器
criterion = torch.nn.MSELoss(size_average=False)
optimizer = torch.optim.SGD(model.parameters(),lr=0.01)


#训练
for epoch in range(100):
    y_pred = model(x_data)
    loss = criterion(y_pred,y_data)
    print(epoch,loss)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()  

#打印训练结果
print('w = ',model.linera.weight.item())
print('b = ',model.linera.bias.item())


#测试模型
x_test = torch.Tensor([[4.0]])
y_test = model(x_test)

print('y_pred = ',y_test.data)