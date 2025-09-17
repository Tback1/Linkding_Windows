python可以用安装版本也可以用内嵌版本，请根据自己需求自行考量

完成python依赖部署后，在 `.env`中部署你的key

## 更新 Npm 依赖

```JavaScript
//更新尤其需要执行 npm更新包
npm install
npm run build
```

## 收集静态文件

```python
..\python\python.exe start.py manage collectstatic --noinput --clear
```

## 测试运行

```python
..\python\python.exe start.py
```
