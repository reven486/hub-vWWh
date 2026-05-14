因为我常用的ide是cursor, 所以这里直接在本地个人用户下新建cursor隐藏文件夹, 这样新建好的是用户级skills,任何项目都可以访问到

cmd中, 如下指令 -> `C:\Users\lenovo>mkdir "%USERPROFILE%\.cursor\skills"` 创建文件夹
而后指令如下, 具体的要求可以参见README中提到的SKILL介绍
```cmd
C:\Users\lenovo>mkdir "%USERPROFILE%\.cursor\skills"

C:\Users\lenovo>mkdir "%USERPROFILE%\.cursor\skills\my-skill"

C:\Users\lenovo>cd "%USERPROFILE%\.cursor\skills\my-skill"

C:\Users\lenovo\.cursor\skills\my-skill>echo #name "This is my first skill" > SKILL.md
```

其他的建立方式:

从 GitHub 安装技能
可以从 GitHub 仓库导入技能：

1. 打开 Cursor Settings → Rules
2. 在 Project Rules 部分，点击 Add Rule
3. 选择 Remote Rule (Github)
4. 输入 GitHub 仓库的 URL

> 后面发现其实可以在cursor settings中直接创建, 并且可以直接选择作用域, 很方便, 那就直接在这里建立了

