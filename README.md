python可以用安装版本也可以用内嵌版本，请自行考虑
js已经编译完毕
完成python依赖部署后，在 `.env`中部署你的key

之后
```python
python.exe manage.py migrate
python.exe manage.py createsuperuser
python.exe -m waitress --port=9090 bookmarks.wsgi:application
```

即可
