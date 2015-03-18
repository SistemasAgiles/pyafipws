Antes de proceder, recomendamos revisar y consultar los siguientes sitios:
  * [Sistemas Ágiles](http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs): soporte comercial pago (asesoramiento inicial gratuito por [email](mailto:facturaelectronica@sistemasagiles.com.ar)). Documentación [Manual de Uso](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs)
  * [Grupo de Usuarios](https://groups.google.com/group/pyafipws?hl=es): novedades, consultas y comentarios generales (foro público abierto, comunitario y gratuito)
  * [Python Argentina](http://www.python.org.ar/pyar/ListaDeCorreo): soporte técnico sobre python comunitario gratuito (por lista de correo, chat, etc.)
  * [Sitio Web del Proyecto](http://www.pyafipws.com.ar/): información técnica y anuncios
  * [Incidencias](http://code.google.com/p/pyafipws/issues/list?can=1&q=&colspec=ID+Type+Status+Priority+Milestone+Owner+Summary&cells=tiles): tickets con consultas o inconvenientes para su resolución.
  * **VIDEO Explicativo Paso a Paso:** ([blip.tv](http://blip.tv/file/4957362) o [youtube](http://www.youtube.com/watch?v=y12qv93c4s8)) sobre instalación en Windows: Python, dependencias y prueba en producción.

**Indice:**



# Instalación desde el código fuente #

Para usar la interfaz y herramientas relacionadas no es necesario compilar ni empaquetar o generar instaladores, simplemente se puede utilizar el código fuente (respetando la licencia [GPLv3](http://code.google.com/p/pyafipws/source/browse/licencia.txt) de software libre), como se describe a continuación:

Descargar el código fuente:
  * Desde [pyafipws-master.zip](https://github.com/reingart/pyafipws/archive/master.zip) (última versión para desarrollo empaquetada de [GitHub](https://github.com/reingart/pyafipws)) **recomendado**
  * ~~Desde [downloads](Descargas.md) (versiones estables), por ejemplo [pyafipws-r108.zip](http://code.google.com/p/pyafipws/downloads/detail?name=pyafipws-r108.zip&can=2&q=) y descomprimir en una carpeta, por ej. pyafipws  GoogleCode no permite nuevas descargas, ver espejo en [GitHub](https://github.com/reingart/pyafipws/releases) para liberaciones recientes
  * Desde el [Repositorio Principal](http://code.google.com/p/pyafipws/source/checkout) (versión de desarrollo, requiere [Mercurial](http://mercurial.selenic.com/)):
```
hg clone https://pyafipws.googlecode.com/hg/ pyafipws 
```~~

Para WSFEv1 y WSMTXCA es necesaria adicionalmente la librería [PySimpleSoap](http://code.google.com/p/pysimplesoap), especificamente la rama [pysimplesoap-reingart.zip](https://pysimplesoap.googlecode.com/archive/reingart.zip) (archivo comprimido)

Para PyRece es necesaria adicionalmente la librería [PyFPDF](http://code.google.com/p/pyfpdf), recomendamos la última versión de desarrollo [pyfpdf.zip](https://pyfpdf.googlecode.com/archive/default.zip) (archivo comprimido)

Para PyI25 (códigos de barra) es requerida la biblioteca [Python Imaging Library](http://www.pythonware.com/products/pil/) (PIL), y también podría usarse [Pillow](https://pypi.python.org/pypi/Pillow/) ("fork" disponible en PyPI)

Nota: Se recomienda bajar las versiones de repositorio de [PyAfipWs](http://code.google.com/p/pyafipws/source/checkout) y [PySimpleSoap](http://code.google.com/p/pysimplesoap/source/checkout) ya que tienen las últimas mejoras.

## GNU/Linux ##

### Debian y derivados (Ubuntu) ###

Instalar dependencias:
```
apt-get install python-httplib2 python-m2crypto
```

Descargar e instalar PySimpleSoap:

```
hg clone https://code.google.com/p/pysimplesoap/ 
cd pysimplesoap
hg update reingart
sudo python setup.py install
```

**Nota:** se recomienda actualizar a la rama _reingart_ ya que la versión de desarrollo tiene algunos temas menores de incompatibilidad por nuevas características que se han agregado y están en revisión. Ejecutar `hg update reingart` como se indica antes de llamar a `setup.py`

Descargar e instalar PyFPDF:

```
hg clone https://code.google.com/p/pyfpdf/ 
cd pyfpdf
sudo python setup.py install
```

Para usar el diseñador visual de plantillas PDF o PyRece, necesitará instalar adicionalmente [wxPython](http://www.wxpython.org/)
```
sudo apt-get install wxpython
```

### Fedora, CentOS, Red-Hat ###

Actualizar Python 2.6 (versiones antiguas vienen con python 2.4 que no es compatible), probado en CentOS release 5.10:

```
wget http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm
rpm -ivh epel-release-5-4.noarch.rpm
yum install python26
```

Instalar dependencia [httplib2](https://code.google.com/p/httplib2/):

```
wget https://httplib2.googlecode.com/files/httplib2-0.8.zip
unzip httplib2-0.8.zip
cd httplib2-0.8
python2.6 setup.py install
```

Instalar librería [pysimplesoap](https://code.google.com/p/pysimplesoap) para  para webservices:

```
wget https://pysimplesoap.googlecode.com/archive/reingart.zip -O pysimplesoap-reingart.zip
unzip pysimplesoap-reingart.zip
cd pysimplesoap-*
python2.6 setup.py install
```

Instalar librería [pyfpdf](https://code.google.com/p/pyfpdf) para PDF:

```
wget https://pyfpdf.googlecode.com/archive/default.zip -O pyfpdf.zip
unzip pyfpdf.zip
cd pyfpdf-*
python2.6 setup.py install
```


## Windows ##

### Instalación automatizada ###

Para facilitar la instalación se proveen dos scripts que automatizan el proceso:

  * [venv.bat](https://code.google.com/p/pyafipws/source/browse/venv.bat): crea un entorno virtual (opcional, ver [abajo](InstalacionCodigoFuente#Entornos_Virtuales_(virtualenv).md))
  * [setup.bat](https://code.google.com/p/pyafipws/source/browse/setup.bat): descarga e instala las dependencias, registrando todos los componentes

Pasos **instalación rápida**:
  1. Descargar [pyafipws-master.zip](https://github.com/reingart/pyafipws/archive/master.zip),  descomprimirlo e ingresar a la carpeta pyafipws-master
  1. Ejecutar `setup.bat` (doble click o por una consola `cmd`)

Se recomienda ejecutarlos como Administrador, y es necesario instalar [Python 2.7.9](https://www.python.org/downloads/windows/) previamente.
Los usuarios avanzados pueden ejecutar previamente `venv.bat` por consola, para crear un entorno virtual.

Para mayor información ver siguientes secciones con los detalles.

### Dependencias ###

Para utilizar este proyecto, desde el código fuente, debe descargar y ejecutar los instaladores de los siguientes requisitos (seleccionar la columna según versión del sistema operativo y arquitectura de CPU):

| **Software a Instalar** | **Python 2.5** (WinXP) | **Python 2.7** (Win7 o sup)  _32 bits_ | **Python 2.7** (Win7 o sup)  _64 bits_  | **Notas** |
|:------------------------|:-----------------------|:---------------------------------------|:----------------------------------------|:----------|
| [Python](http://www.python.org) (lenguaje programación) | [Python 2.5.4](http://www.python.org/ftp/python/2.5.4/python-2.5.4.msi) | [Python 2.7.9](http://www.python.org/ftp/python/2.7.9/python-2.7.9.msi) | [Python 2.7.9 "amd64"](https://www.python.org/ftp/python/2.7.9/python-2.7.9.amd64.msi) | soporte para Python 3.x próximamente |
| [OpenSSL](https://www.openssl.org/) (seguridad SSL/TLS) | [Win32OpenSSL 0.9.7m](http://www.sistemasagiles.com.ar/soft/Win32OpenSSL-0_9_8i.exe) `**` | [Win32OpenSSL 1.0.1L](http://slproweb.com/download/Win32OpenSSL-1_0_1L.exe) | [Win64OpenSSL 1.0.1L](http://slproweb.com/download/Win64OpenSSL-1_0_1L.exe) | opcional, solo necesario para generar certificados / compilar M2Crypto|
| [M2Crypto](http://chandlerproject.org/Projects/MeTooCrypto) (OpenSSL para Python) | [inst. v0.18.2](http://www.sistemasagiles.com.ar/soft/pyafipws/M2Crypto-0.18.2.win32-py2.5.exe) `**` |  [inst. v0.22.3](http://www.sistemasagiles.com.ar/soft/pyafipws/M2Crypto-0.22.3.win32-py2.7.exe) `*` | [inst. v0.21.1 "amd64"](http://chandlerproject.org/pub/Projects/MeTooCrypto/M2Crypto-0.21.1.win-amd64-py2.7.exe) | o superior, salvo 0.19 no funcionaba correctamente |
| [httplib2](https://github.com/jcgregorio/httplib2) (biblioteca conexión HTTP) | [fuentes v0.4.0](http://httplib2.googlecode.com/files/httplib2-0.4.0.zip) | [inst. v0.9](http://www.sistemasagiles.com.ar/soft/pyafipws/httplib2-0.9.win32.exe) `*` | [inst. v0.9 "amd64"](http://www.sistemasagiles.com.ar/soft/pyafipws/httplib2-0.9.win-amd64.exe) `*`| Para instalar las fuentes, descomprimir y ejecutar por línea de comando: `c:\python25\python.exe setup.py install` |
| [Extensiones Windows](http://starship.python.net/crew/mhammond/win32/) para interfase COM | [pywin32](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py2.5.exe/download) | [inst. v219](http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win32-py2.7.exe) | [inst. v219 "amd64"](http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win-amd64-py2.7.exe) | opcional, solo para comunicación con VB, VFP, .NET, Java y similares |
| [PySimpleSOAP](https://code.google.com/p/pysimplesoap/) (webservices) | [fuentes](https://pysimplesoap.googlecode.com/archive/reingart.zip) (zip) | [inst. v1.08d](https://pypi.python.org/packages/any/P/PySimpleSOAP/PySimpleSOAP-1.08d.win32.exe) (PyPI) | [inst. v1.08d "amd64"](https://pypi.python.org/packages/any/P/PySimpleSOAP/PySimpleSOAP-1.08d.win-amd64.exe) (PyPI)  | Ver abajo para versiones actualizadas |
| [PyFPDF](https://code.google.com/p/pyfpdf/) (generación PDF) | [fuentes](https://pyfpdf.googlecode.com/archive/default.zip) (zip) | [inst. v1.7.2](https://pypi.python.org/packages/any/f/fpdf/fpdf-1.7.2.win32.exe) (PyPI) | [inst. v1.7.2 "amd64"](https://pypi.python.org/packages/any/f/fpdf/fpdf-1.7.2.win-amd64.exe) (PyPI) | Ver abajo para versiones actualizadas |
| [PIL / Pillow](https://code.google.com/p/pyfpdf/) (imágenes) | [inst. v1.1.7](http://effbot.org/downloads/PIL-1.1.7.win32-py2.5.exe) | [inst. v1.1.7](http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe) | [inst. v2.7.0 "amd64"](https://pypi.python.org/packages/2.7/P/Pillow/Pillow-2.7.0.win-amd64-py2.7.exe#md5=df1219055fea2d34370a56efd8d27b29) (PyPI) | solo necesario para generación de imágenes |

**Notas**:

  * Algunos paquetes (marcados con asterisco `*`) se han compilado y subido a nuestro servidor para facilitar la instalación a los nuevos usuarios. Por favor dirigirse al sitio de cada proyecto para obtener los paquetes oficiales o mayor información.
  * Ciertos paquetes son versiones históricas (marcados con dos asteriscos `**`), alojados para compatibilidad hacia atrás.
  * Se recomienda **Python 2.7.9** para nuevas instalaciones, ya que incorpora las últimas características y cubre los recientes temas de seguridad.
  * Las versiones "amd64" también funcionan para arquitecturas Intel x86 64 bits (se utiliza la denominación original).

#### Desarrollo ####

Para obtener el código fuente de las dependencias principales (en especial para los contribuidores que deseen realizar ajustes), recomendamos clonar una versión actualizada desde el repositorio.

**Nota:** este paso no es necesario si el paquete se ha instalado según las instrucciones en las secciones previas.

Para PySimpleSoap, realizar los siguientes pasos:

```
hg clone https://code.google.com/p/pysimplesoap/ 
cd pysimplesoap
hg update reingart
c:\python25\python.exe setup.py install
```

Ver nota sobre rama _reingart_ en sección anterior.

Ídem para PyFPDF:

```
hg clone https://code.google.com/p/pyfpdf/ 
cd pyfpdf
c:\python25\python.exe setup.py install
```

#### Adicionales ####

Para soporte proxy avanzado instalar [ScksiPy](http://sourceforge.net/projects/socksipy) y copiar `socks.py` en `C:\Python25\Lib\site-packages` Opcional (no sería necesario para python 2.7).
Recomendamos [PyCurl](http://pycurl.sourceforge.net/) para cuestiones avanzadas y esquemas de autenticación propietaria (compatibilidad con MS ISA Server)


Para usar el diseñador visual de plantillas PDF o PyRece, necesitará instalar adicionalmente [wxPython](http://www.wxpython.org/) ([versión 2.8.10.1 para Python 2.5](http://sourceforge.net/projects/wxpython/files/wxPython/2.8.10.1/wxPython2.8-win32-unicode-2.8.10.1-py25.exe/download))

Para usar la tablas de intercambio dbf (dBase, Clipper, Fox Pro, etc.) se debe instalar [dbf 0.88.019](http://www.sistemasagiles.com.ar/soft/pyafipws/dbf-0.88.019-python.zip) o superior (descomprimirla en la carpeta de pyafipws, y los .py deben quedar adentro de la subcarpeta dbf). Ver el paquete actualizado en [PyPI](https://pypi.python.org/pypi/dbf) para versiones posteriores

**NOTA**: Se recomienda revisar los sitios en búsqueda de actualizaciones que pudieran corresponder, y verificar que la versión de la biblioteca descargada es compatible con la versión de Python elegida.

### Registración ###

Para registrar el Servidor COM y poder acceder desde otros lenguajes ejecutar:
```
c:\python25\python.exe pyafipws.py --register
c:\python25\python.exe wsaa.py --register
c:\python25\python.exe wsfev1.py --register
c:\python25\python.exe wsmtx.py --register
c:\python25\python.exe wsfexv1.py --register
c:\python25\python.exe wscoc.py --register
c:\python25\python.exe wsctg11.py --register
c:\python25\python.exe wslpg.py --register
c:\python25\python.exe cot.py --register
c:\python25\python.exe trazamed.py --register
```

**NOTA**: `pyafipws.py` es obsoleto y se mantiene por compatibilidad, utilizar los nuevos componentes modulares (`wsaa.py`, `wsfev1.py`, etc.)

### Generación de Instalador ###

Instalar [py2exe](http://sourceforge.net/projects/py2exe/files/).

Para los nuevos instaladores para Windows es necesario tener Nullsoft Scriptable Install System (NSIS):
http://nsis.sourceforge.net/Main_Page

Para generar los nuevos instaladores revisar el script de instalación [setup.py](https://code.google.com/p/pyafipws/source/browse/setup.py) y ejecutar:
```
c:\python25\python.exe setup.py py2exe
```

Ver documentación del nuevo instalador en [Manual](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#Instalación) (pasos, opciones e instalación desatendida).

Para el instalador antiguo (desaconsejado ya que es obsoleto y no soporta todos los servicios web), ejecutar el archivo https://code.google.com/p/pyafipws/source/browse/build-pyafipws.bat?name=c14809235349&r=db92558ef8c8778632404769f4e91a2c7ab1209d incluido dentro del código fuente. Dicho archivo genera los mismos instaladores todo-en-uno distribuidos por este proyecto.

Para armar el paquete comprimido autoextraible se requiere la herramienta [7-zip](http://www.7-zip.org/):
  * [7za465.zip](http://downloads.sourceforge.net/sevenzip/7za465.zip) (compresor 7z.exe por linea de comando)
  * [7za914.zip](http://downloads.sourceforge.net/project/sevenzip/7-Zip/9.14/7za914.zip) (extras para autoextractor 7zSD.sfx)

# Uso en Producción #

Por diseño, la interfaz COM (`pyafipws.py`, `wsaa.py`) y herramientas (`rece.py`, `recex.py` y `receb.py`) funcionan en modo homologación, para habilitar modo producción, por ej. editar la linea [#28](http://code.google.com/p/pyafipws/source/browse/pyafipws.py#28):
```
HOMO = True
```
y cambiarla a:
```
HOMO = False
```

De lo contrario, la interfaz no tendrá en cuenta las URLs de los servidores de Producción, aunque sean informadas en CallWSAA y Conectar.

**Nota**: Esto no aplica a los módulos para Python (`wsfev1.py`, `wsfexv1.py`, etc.), pero también por defecto funcionan con URL de homologación.

Lo mismo aplica para WSFEv1 y WSMTXCA.

# Entornos Virtuales (virtualenv) #

Los siguientes comandos clonan el repositorio, crean un virtualenv e instalan los paquetes requeridos (incluyendo las últimas versiones de las dependencias) para evitar conflictos con otras bibliotecas.

## venv en GNU/Linux ##

Ejemplo para Debian/Ubuntu (abrir una terminal y ejecutar los comandos):

```
sudo apt-get install python-dev swig python-virtualenv mercurial python-pip libssl-dev
hg clone https://code.google.com/p/pyafipws
cd pyafipws
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## venv en Windows ##

Para Windows es similar, ver pre-requisitos [arriba](#Windows.md):
  * descargar [get-pip.py](https://raw.github.com/pypa/pip/master/contrib/get-pip.py) y ejecutarlo (doble-click). **Nota:** Sólo versiones antiguas de Python (menor a 2.7.9) que no tengan `pip` incorporado
  * abrir una consola de comandos (`cmd`) y ejecutar `pip.exe install wheel`
  * abrir una consola de comandos (`cmd`) y ejecutar `pip.exe install virtualenv`

Para compilar las dependencias binarias -M2Crypto-, instalar adicionalmente:
  * [Microsoft Visual C++ Compiler for Python 2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266)
  * [SWIG](http://www.swig.org/)


Ejemplo para Windows (instalar previamente [Python 2.7.9](https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi) y ejecutar los siguientes comandos en una consola `cmd`):

Instalar utilidades de instalación / entorno virtual:

```
pip install --upgrade pip
pip install --upgrade wheel
pip install --upgrade virtualenv
```

Crear y activar el entorno virtual venv (en el directorio actual)
```
virtualenv venv
venv\Scripts\activate
```

Instalar las dependencias binarias (precompiladas):
```
pip install http://www.sistemasagiles.com.ar/soft/pyafipws/M2Crypto-0.22.3-cp27-none-win32.whl
pip install http://www.sistemasagiles.com.ar/soft/pyafipws/pywin32-219-cp27-none-win32.whl
```

Instalar el resto de los requerimientos:
```
pip install -r requirements.txt
```