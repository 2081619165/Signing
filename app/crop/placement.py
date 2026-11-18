"""Windows原生定位，所有边界均使用WinForms同一坐标系。"""

def choose_bounds(main,area,size):
    x,y,mw,mh=main;left,top,aw,ah=area
    width=min(size[0],aw);height=min(size[1],ah)
    # 先相对主窗口居中，再夹紧到工作区；保持现有尺寸限制。
    px=x+(mw-width)//2;py=y+(mh-height)//2
    return (max(left,min(px,left+aw-width)),max(top,min(py,top+ah-height)),width,height)


def activate(window):
    from System import Action
    from System.Windows.Forms import FormWindowState
    form=window.native
    if form is None:return
    def action():
        if form.IsDisposed:return
        if form.WindowState==FormWindowState.Minimized:form.WindowState=FormWindowState.Normal
        form.Show();form.BringToFront();form.Activate()
    form.Invoke(Action(action))


def show_positioned(window,parent,record=None):
    from System import Action
    from System.Drawing import Rectangle,Size
    from System.Windows.Forms import Screen,FormWindowState
    form=window.native
    def action():
        if record:record("winforms_enter")
        main=parent.native
        area=Screen.FromControl(main).WorkingArea
        bounds=main.Bounds
        # 仅默认大小由DIP换成原生像素，坐标不再交回PyWebView二次缩放。
        scale=float(main.DeviceDpi)/96
        rect=choose_bounds((bounds.X,bounds.Y,bounds.Width,bounds.Height),
            (area.X,area.Y,area.Width,area.Height),(round(900*scale),round(650*scale)))
        form.WindowState=FormWindowState.Normal
        form.MinimumSize=Size(min(form.MinimumSize.Width,rect[2]),min(form.MinimumSize.Height,rect[3]))
        if record:record("position_ready",bounds=list(rect),dpi=int(main.DeviceDpi))
        form.Bounds=Rectangle(*rect)
        form.Show();form.BringToFront();form.Activate()
        if record:record("visible_state",visible=bool(form.Visible),focused=bool(form.ContainsFocus))
    if record:record("winforms_invoke_begin")
    form.Invoke(Action(action))
    if record:record("winforms_invoke_end")
