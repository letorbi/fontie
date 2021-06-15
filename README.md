# Fontie

The deamon that is running in the back of [Fontie](https://fontie.pixelsvsbytes.com). The backend
is where all the font conversion "magic" happens. The frontend is just an interface to upload the
font-files and trigger the genration of the font-package by the backend.

The Fontie backend is licensed as open source under the AGPL v3.

# Installation

This guide assumes that you are simply trying to run fontie on your own Linux/UNIX-ish computer. This guide is a work in progress and not guaranteed to work.

## dependencies 

These MUST be installed before you attempt to convert a font with fontie!!

  - `fontforge` python package
     - See "using fontforge as a python package"
  - `ttfautohint`
     - `apt install -y ttfautohint` worked for me.
     - you can download source from https://download.savannah.gnu.org/releases/freetype/ in case you can't find a pre-built package for your system.
     - test your installation by running `ttfautohint`
  - `/opt/woff2/woff2_compress`
     - I downloaded this from https://github.com/google/woff2 with `cd /opt && git clone https://github.com/google/woff2 && cd woff2`
     - In order to build this, you need to initialize and pull the git submodules. `git submodule init && git submodule update brotli`
     - finally, in order to build it, run `make`.
     - test it by running `/opt/woff2/woff2_compress`
  - `scour`
     - sudo apt install scour
  - `wine /opt/eotfast/EOTFAST-1.EXE`
     - this is only required for building eot fonts (internet explorer) 
     - TODO how to install this is undocumented 
    

## obtaining fontie

First, clone the fontforge repository:

```
# some scripts in the source code are hard-coded to /opt/fontie. So we clone the repo there.
cd /opt
git clone https://github.com/ForestJohnson/fontie 
cd fontie
pipenv install
```

## using fontforge as a python package

You can't actually install fontforge python package via pip! https://github.com/fontforge/fontforge/issues/4377
So you have to install it via your OS package manager. 

For (ubuntu/debian):

```
sudo apt-get install fontforge
```

NOTE: According to https://fontforge.org/docs/scripting/python.html#python-extension  

> In python terms fontforge _embeds_ python, It is possible to build fontforge so that it is also a python extension.
>
> ...
>
> fontforge typically installs a Python module accessible to the system’s python executable, which can be accessed using:
> 
> ```
> import fontforge
> ```

However, if you run `python3 bin/fontie.py` you might get:

```
ModuleNotFoundError: No module named 'fontforge'
```

We can sidestep this problem by running the fontie API server through the fontforge embedded python:

```
fontforge -lang=py -script bin/fontie.py 
```

# Using Fontie Locally 

TODO How to set up your own fontie server that other people can use is undocumented right now.

## Sending a request using cURL

The following was obtained from https://fontie.pixelsvsbytes.com/webfont-generator by clicking `Generate & download your @font-face package`  and then opening the browser debugger to the network tab, right clicking the POST request, and choosing "copy as cURL":

`curl 'https://fontie.pixelsvsbytes.com/fontie.server/package/' -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: multipart/form-data; boundary=---------------------------286836418736644408031661354643' -H 'Origin: https://fontie.pixelsvsbytes.com' -H 'Connection: keep-alive' -H 'Referer: https://fontie.pixelsvsbytes.com/webfont-generator' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data-binary $'-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="font"\r\n\r\nfont_2c96d373-0dc3-4292-a288-5129f9774947\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\nwoff\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\nwoff2\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\notf\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="lang"\r\n\r\non\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="ranges"\r\n\r\n0020-007F,20AC\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="ranges"\r\n\r\n00A0-00FF\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="hinting"\r\n\r\nnohint\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nmetrics\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nglyphs\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nreferences\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nname\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="css"\r\n\r\ncreate\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="html"\r\n\r\ncreate\r\n-----------------------------286836418736644408031661354643--\r\n'`

Fontie runs on port 8000 by default. So we can modify this curl command by changing `https://fontie.pixelsvsbytes.com/fontie.server/package/` to `localhost:8000/package/` in order to send the command to my local fontie instance instead of the hosted one. 

Also, the `name="font"\r\n\r\nfont_2c96d373-0dc3-4292-a288-5129f9774947\r\n` part referrs to a font which was previously uploaded. 

in `FontieFont.py` you can see `FONT_ROOT = "/tmp"` and 

```
    def open(self, id):
        path = os.path.join(FONT_ROOT, id)
        orig = "%s_orignal" % path
```

So it looks like the temporary file for the uploaded font is named `/tmp/font_2c96d373-0dc3-4292-a288-5129f9774947_orignal` when we are using the hosted https://fontie.pixelsvsbytes.com/webfont-generator server. 

Therefore, in this example, we simply copy the desired font (ttf file, or other input font file) to that path:

```
cp ~/Desktop/fonts/Blackpine-4BEVW.ttf /tmp/font_2c96d373-0dc3-4292-a288-5129f9774947_orignal
```

We can also get rid of the not-needed http headers, yielding the following command: 

`curl -X POST -v 'localhost:8000/package/' -H 'Content-Type: multipart/form-data; boundary=---------------------------286836418736644408031661354643' --data-binary $'-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="font"\r\n\r\nfont_2c96d373-0dc3-4292-a288-5129f9774947\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\nwoff\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\nwoff2\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="output"\r\n\r\notf\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="lang"\r\n\r\non\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="ranges"\r\n\r\n0020-007F,20AC\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="ranges"\r\n\r\n00A0-00FF\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="hinting"\r\n\r\nnohint\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nmetrics\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nglyphs\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nreferences\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="fixes"\r\n\r\nname\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="css"\r\n\r\ncreate\r\n-----------------------------286836418736644408031661354643\r\nContent-Disposition: form-data; name="html"\r\n\r\ncreate\r\n-----------------------------286836418736644408031661354643--\r\n'`

While running, you may see some logs like 

```
Internal Error (overlap) in u: Humph. This monotonic leads nowhere (81,137)->(81.0025,137.145).
Internal Error (overlap) in u: couldn't find a needed exit from an intersection
Internal Error (overlap) in u: Humph. This monotonic leads nowhere (127.473,235.473)->(127,237).
Internal Error (overlap) in u: couldn't find a needed exit from an intersection
```

Coming from the fontie server process. It may take a minute or two to finish.

When it ran successfully, this curl command returned: 

```
{"package":"fontie_707d50ce-8998-4e85-b391-d788fe57c8d8"}
```

Finally, we can move the resulting folder to the desktop like so:

```
mv /tmp/fontie_707d50ce-8998-4e85-b391-d788fe57c8d8/fontie-package ~/Desktop/Blackpine-Processed
```

----

Copyright 2013-2018 Torben Haase \<https://pixelsvsbytes.com>
