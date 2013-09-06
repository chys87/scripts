"
" Copyright (c) 2013, chys <admin@CHYS.INFO>
"
" Redistribution and use in source and binary forms, with or without
" modification, are permitted provided that the following conditions
" are met:
"
"   Redistributions of source code must retain the above copyright notice, this
"   list of conditions and the following disclaimer.
"
"   Redistributions in binary form must reproduce the above copyright notice,
"   this list of conditions and the following disclaimer in the documentation
"   and/or other materials provided with the distribution.
"
"   Neither the name of chys <admin@CHYS.INFO> nor the names of other
"   contributors may be used to endorse or promote products derived from
"   this software without specific prior written permission.
"
" THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
" IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
" ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
" LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
" CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
" SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
" INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
" CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
" ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
" POSSIBILITY OF SUCH DAMAGE.
"


" Enable Pathogen (https://github.com/tpope/vim-pathogen) if we have it.
" Also see my question on StackOverflow:
" http://stackoverflow.com/questions/18576651/check-whether-pathogen-is-installed-in-vimrc
runtime! autoload/pathogen.vim
if exists("*pathogen#infect")
	call pathogen#infect()
endif


syntax on

"let Tlist_Use_Right_Window=1
"let Tlist_File_Fold_Auto_Close=0
"set wrap	(This is the default)"
set fenc=utf-8 "Default coding
set fencs=ucs-bom,utf-8,gb18030,iso-8859-15,default "Coding used to open a file

set nu "Display line number

set viminfo="" " Disable viminfo

set autoindent
set smartindent
set cindent
set tabstop=4
set softtabstop=4
set shiftwidth=4
"set showmatch          " Briefly jump to the pair when inserting a bracket
set showmode           " On by default. Reiterate.
set wildmenu           " Show a menu of files then pressing tab
set wildmode=full
set mouse=a
set backspace=indent,eol,start " More liberal use of backspace

colorscheme delek
"colorscheme louver
if (has("gui_running"))
	set guifont=MonoSpace\ 8
	"set guifont=DejaVu\ Sans\ Mono\ 8

	" Maximize window
	com MX silent !wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz

	" General options
	set guioptions-=T "Hide toolbar
	set guioptions-=m "Hide menu
endif

set hlsearch     " Debian/Ubuntu turns it off by default
set modeline     " Override Gentoo default and enable modeline
set incsearch
set smartcase

filetype plugin indent on

let c_gnu=1
let c_no_curly_error=1      " ({}) is not an error
"let c_space_errors=1        " Mixed space and tab is error.
let g:load_doxygen_syntax=1

"Enable NeoComplCache
"let g:neocomplcache_enable_at_startup = 1
let g:neocomplcache_enable_auto_select = 1
com NC NeoComplCache

" OmniComplete options
"let OmniCpp_NamespaceSearch = 1

""Enable folding by syntax (zc/zo/zC/zO)
"set foldlevelstart=99 "Don't fold when a file is opened
"set foldmethod=syntax
"set foldcolumn=6

"if (has("gui_running"))
"	set list listchars=tab:\>\ ,eol:$
"endif

" Navigate between tabs more easily
nmap <Tab> :tabn<CR>
nmap <C-Tab> :tabn<CR>
nmap <S-Tab> :tabp<CR>

" Define Ctrl-\ to open definition in a new tab
map <C-\> :tab split<CR>:exec("tag ".expand("<cword>"))<CR>

"let g:winManagerWindowLayout='FileExplorer|TagList'
"let g:winManagerWidth=40
"nmap <F3> :WMToggle<cr>

"if (has("gui_running"))
"	set cursorcolumn
"	set cursorline
"endif

"behave mswin

"set spell

"set wildmode=list:full
"set wildmenu

" Session options
set sessionoptions=sesdir,tabpages
com SL source Session.vim
com SX call SessionSaveAndExit()
function SessionSaveAndExit()
	wa
	mks!
	qa
endfunction


" localvimrc (https://github.com/embear/vim-localvimrc) config
let g:localvimrc_ask=0  "Silently load local vimrc files
let g:localvimrc_sandbox=0  " Don't run them in a sand box


" Strip trailing spaces
"autocmd FileType c,cpp,python,java,php autocmd BufWritePre <buffer> :%s/\s\+$//e

autocmd FileType markdown setl ts=8 sts=4 sw=4 expandtab


" Source configurations specific to one machine
if filereadable(expand("~/.vimrc.local"))
	source ~/.vimrc.local
endif
