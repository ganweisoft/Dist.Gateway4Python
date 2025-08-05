## GWMiniDataCenter-Python

该项目是分离自GateWay(下称GateWay)(https://github.com/ganweisoft/Gateway)的一个可扩展的, 开发自.NET框架的微型网关.
作用是适配其他主流的开发语言, 使得开发者可以使用自己熟悉的开发语言进行开发. 
消息通道使用的是dapr(https://docs.dapr.io/).

### 消息路径

使用dapr的消息通道, 传输设备的实时值到GateWay主网关. 架构图:   
![img.png](img.png)

1. GateWay主网关作为subscriber. 
2. 消息队列中间件可选MQTT, kafka, redis等.
3. Java/Python/.NET版本的Mini-GateWay作为publisher.

**Java版Mini-GateWay仓库: (https://github.com/ganweisoft/Mini-Gateway-Java.git)**  
**.NET版Mini-GateWay仓库: (https://github.com/ganweisoft/Mini-Gateway-CSharp.git)**

### 内部扩展

1. 同GateWay一样, 可进行内部扩展. 只需继承CEquipBase, 将类名命名为CEquip.
生成的文件放入GWHost1的上层目录的dll目录下.
GWMiniDataCenter启动是即可自扫描加载.
```python
if __name__ == '__main__':
    from ganweisoft.DataCenter import DataCenter

    DataCenter.start()
```
