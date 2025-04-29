import webbrowser

keys = ['ночь Сергея Параджанова в свободном пространстве «Циферблат»']
for key in keys:
    webbrowser.open_new_tab('https://www.google.ru/search?q='+ key +'&newwindow=1&espv=2&source=lnms&tbm=isch&sa=X')