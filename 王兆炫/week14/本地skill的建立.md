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

<img width="1111" height="689" alt="image" src="https://github.com/user-attachments/assets/42889048-6782-4634-976e-5d5ec8cece66" />

直接在settings页面发起创建即可，会自动在项目中创建SKILLS文件夹

而后就可以找到对应的skills
<img width="527" height="125" alt="image" src="https://github.com/user-attachments/assets/3eb00100-ad35-45f2-a34d-69be5283d6db" />

详见对应的`stock-volatility-visualization.md`文件, 注意实际使用时需要放在 `.cursor/skills/` 目录下
