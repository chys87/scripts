# chys-scripts #

## 列表 ##

* `android-power.sh`: 通过ADB模拟按Android的电源键
* `android-screencap.sh`: 通过ADB对Android进行截屏
* `daemon-run.py`: 异步执行命令
* `gentoo`: [Gentoo](http://gentoo.org/) 专用脚本
    * `etc-portage-bashrc`: 我的 `/etc/portage/bashrc` 文件
    + `view-ebuild.sh` (bash): 快速查看 Gentoo 的 ebuild 文件
* `gitconfig`: 我的 [Git 配置文件](https://www.kernel.org/pub/software/scm/git/docs/git-config.html)
* `githooks`: 一些有用的 [git hooks](http://www.git-scm.com/book/en/Customizing-Git-Git-Hooks)
* `greasemonkey`: [Greasemonkey](http://www.greasespot.net)/[Tampermonkey](http://tampermonkey.net/) 脚本
* `guess-ssh-agent.sh`: 在 [tmux](http://tmux.sourceforge.net/) 或 [screen](http://www.gnu.org/software/screen/) 中使用正确的 `$SSH_AUTH_SOCK` 调用其他程序
* `idfinal.py` (Python 2.7/3.2): 计算或验证中国身份证号码的最后一位
* `init-iptables`: 初始化iptables
* `json_pprint.py` (Python 3.2+): 简单粗暴的 JSON 格式化工具，支持一部分非标准 JSON 格式
* `mdqp.py` (Python 2.7/3.3): [Markdown](http://en.wikipedia.org/wiki/Markdown) 格式文档快速查看器
* `mvln.py` (Python 3): 移动和链接文件
* `passgen.py` (Python 2.7/3): 随机密码生成器
* `salary-calc.py` (Python 3.2+): 一个简单的中国社保、个人所得税计算器
* `shellrc`: 我的 shell 配置文件 (bash/[zsh](http://www.zsh.org) 通用)
    + 注: 这个文件不能直接作为 `.bashrc` 或 `.zshrc` 文件, 而应在 `.bashrc`/`.zshrc` 末尾 source
* `sys-init`: 我的系统初始化脚本
* `tmux.conf`: 我的 [tmux](http://tmux.sourceforge.net/) 配置文件
* `update-cygwin-installer.py`: 自动更新Cygwin安装程序
* `urlunescape.py` (Python 3): 一个简单的 URL 解码脚本，支持 UTF-8 和 GB18030
* `vimrc`: 我的 `.vimrc` 文件
* `external/*`: 其他人写的有用脚本 (版权属于原作者)

更多信息，请参见脚本源代码及帮助信息。

## List ##

* `android-power.sh`: Send the power button event to Android via ADB
* `android-screencap.sh`: Make screenshot of Android via ADB
* `daemon-run.py`: Run commands asynchronously
* `gentoo`: [Gentoo](http://gentoo.org/)-specific scripts
    * `etc-portage-bashrc`: My `/etc/portage/bashrc`
    + `view-ebuild.sh` (bash): View ebuild files of Gentoo Linux
* `gitconfig`: My [Git config file](https://www.kernel.org/pub/software/scm/git/docs/git-config.html)
* `githooks`: Some useful [git hooks](http://www.git-scm.com/book/en/Customizing-Git-Git-Hooks)
* `greasemonkey`: [Greasemonkey](http://www.greasespot.net)/[Tampermonkey](http://tampermonkey.net/) scripts
* `guess-ssh-agent.sh`: Call external progrms with correct `$SSH_AUTH_SOCK` from [tmux](http://tmux.sourceforge.net/) 或 [screen](http://www.gnu.org/software/screen/) sessions
* `idfinal.py` (Python 2.7/3.2): Calculate or verify the last digit of a Chinese ID number
* `init-iptables`: Initialize iptables
* `json_pprint.py` (Python 3.2+): Quick and dirty JSON pretty printer, supporing some nonstandard JSON
* `mdqp.py` (Python 2.7/3.3): A quick previewer for [Markdown](http://en.wikipedia.org/wiki/Markdown) documentation
* `mvln.py` (Python 3): Move and symlink file
* `passgen.py` (Python 2.7/3): Random password generator
* `salary-calc.py` (Python 3.2+): A simple Chinese social security and income tax calculator
* `shellrc`: My shell configuration file (compatible with both bash and [zsh](http://www.zsh.org))
    - Note: This file shouldn't be directly used as `.bashrc` or `.zshrc`, but sourced at the end of them.
* `sys-init`: My system initialization scripts
* `tmux.conf`: My [tmux](http://tmux.sourceforge.net/) configuration file
* `update-cygwin-installer.py`: Update Cygwin installer automatically
* `urlunescape.py` (Python 3): A simple URL decoder, supporting UTF-8 and GB18030
* `vimrc`: My `.vimrc` file
* `external/*`: Useful scripts written by others (copyright may be reserved by the original authors)

For more information, please refer to the source code and help info of the scripts.

## Contact ##

E-mail: `admin`(at)`CHYS`(dot)`INFO`
