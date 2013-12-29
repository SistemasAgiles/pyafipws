#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para obtener código de trazabilidad de granos
del web service WSCTG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.10a"

LICENCIA = """
wsctg11.py: Interfaz para generar Código de Trazabilidad de Granos AFIP v1.1
Copyright (C) 2012 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA="""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una CTG de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)

  --dummy: consulta estado de servidores
  --solicitar: obtiene el CTG (según archivo de entrada en TXT o CSV)
  --confirmar: confirma el CTG (según archivo de entrada en TXT o CSV)
  --anular: anula el CTG
  --rechazar: permite al destino rechazar el CTG
  --confirmar_arribo: confirma el arribo de un CTG
  --confirmar_definitivo: confirma el arribo definitivo de un CTG

  --consultar: consulta las CTG generadas
  --consultar_excel: consulta las CTG generadas (genera un excel)
  --consultar_detalle: obtiene el detalle de una CTG
  --consultar_constancia_pdf: descarga el documento PDF de una CTG
  
  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --especies: obtiene el listado de especies
  --cosechas: obtiene el listado de cosechas

Ver wsctg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, base64
from php import date
import traceback
from pysimplesoap.client import SoapFault
import utils

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir


WSDL = "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v1.1?wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wsctg.ini"
HOMO = False

# definición del formato del archivo de intercambio:

ENCABEZADO = [
    # datos enviados
    ('tipo_reg', 1, A), # 0: encabezado
    ('numero_carta_de_porte', 13, N),
    ('codigo_especie', 5, N),
    ('cuit_canjeador', 11, N), 
    ('cuit_destino', 11, N), 
    ('cuit_destinatario', 11, N), 
    ('codigo_localidad_origen', 6, N), 
    ('codigo_localidad_destino', 6, N), 
    ('codigo_cosecha', 4, N), 
    ('peso_neto_carga', 5, N), 
    ('cant_horas', 2, N), 
    ('patente_vehiculo', 6, A), 
    ('cuit_transportista', 11, N), 
    ('km_recorridos', 4, N),     
    ('establecimiento', 6, N),             # confirmar arribo
                     
    # datos devueltos
    ('numero_ctg', 8, N), 
    ('fecha_hora', 19, A), 
    ('vigencia_desde', 10, A), 
    ('vigencia_hasta', 10, A), 
    ('transaccion', 12, N), 
    ('tarifa_referencia', 6, I, 2),           # consultar detalle
    ('estado', 20, A), 
    ('imprime_constancia', 5, A), 
    ('observaciones', 200, A), 
    ('errores', 1000, A),
    ('controles', 1000, A),
    ]        



class WSCTG11(BaseWS):
    "Interfaz para el WebService de Código de Trazabilidad de Granos"    
    _public_methods_ = ['Conectar', 'Dummy',
                        'SolicitarCTGInicial', 'SolicitarCTGDatoPendiente',
                        'ConfirmarArribo', 'ConfirmarDefinitivo',
                        'AnularCTG', 'RechazarCTG', 
                        'ConsultarCTG', 'LeerDatosCTG', 'ConsultarDetalleCTG',
                        'ConsultarCTGExcel', 'ConsultarConstanciaCTGPDF',
                        'ConsultarProvincias', 
                        'ConsultarLocalidadesPorProvincia', 
                        'ConsultarEstablecimientos',
                        'ConsultarCosechas',
                        'ConsultarEspecies',
                        'AnalizarXml', 'ObtenerTagXml',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback',
        'NumeroCTG', 'CartaPorte', 'FechaHora', 'CodigoOperacion', 
        'CodigoTransaccion', 'Observaciones', 'Controles', 'DatosCTG',
        'VigenciaHasta', 'VigenciaDesde', 'Estado', 'ImprimeConstancia',
        'TarifaReferencia',
        ]
    _reg_progid_ = "WSCTG11"
    _reg_clsid_ = "{ACDEFB8A-34E1-48CF-94E8-6AF6ADA0717A}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def inicializar(self):
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.CodError = self.DescError = ''
        self.NumeroCTG = self.CartaPorte = ""
        self.CodigoTransaccion = self.Observaciones = ''
        self.FechaHora = self.CodigoOperacion = ""
        self.VigenciaDesde = self.VigenciaHasta = ""
        self.Controles = []
        self.DatosCTG = self.TarifaReferencia = None
        self.CodigoTransaccion = self.Observaciones = ''

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores'] or []
            self.Errores = [err['error'] for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    def __analizar_controles(self, ret):
        "Comprueba y extrae controles si existen en la respuesta XML"
        if 'arrayControles' in ret:
            controles = ret['arrayControles']
            self.Controles = ["%(tipo)s: %(descripcion)s" % ctl['control'] 
                                for ctl in controles]

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['response']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def AnularCTG(self, carta_porte, ctg):
        "Anular el CTG si se creó el mismo por error"
        response = self.client.anularCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosAnularCTG={
                            'cartaPorte': carta_porte,
                            'ctg': ctg, }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['CTG'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def RechazarCTG(self, carta_porte, ctg, motivo):
        "El Destino puede rechazar el CTG a través de la siguiente operatoria"
        response = self.client.rechazarCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosRechazarCTG={
                            'cartaPorte': carta_porte,
                            'ctg': ctg, 'motivoRechazo': motivo,
                            }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['CTG'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def SolicitarCTGInicial(self, numero_carta_de_porte, codigo_especie,
        cuit_canjeador, cuit_destino, cuit_destinatario, codigo_localidad_origen,
        codigo_localidad_destino, codigo_cosecha, peso_neto_carga, 
        cant_horas=None, patente_vehiculo=None, cuit_transportista=None, 
        km_recorridos=None, **kwargs):
        "Solicitar CTG Desde el Inicio"
        # ajusto parámetros según validaciones de AFIP:
        if cuit_canjeador and int(cuit_canjeador) == 0:
            cuit_canjeador = None         # nulo
        ret = self.client.solicitarCTGInicial(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                         datosSolicitarCTGInicial=dict(
                            cartaPorte=numero_carta_de_porte, 
                            codigoEspecie=codigo_especie,
                            cuitCanjeador=cuit_canjeador or None, 
                            cuitDestino=cuit_destino, 
                            cuitDestinatario=cuit_destinatario, 
                            codigoLocalidadOrigen=codigo_localidad_origen,
                            codigoLocalidadDestino=codigo_localidad_destino, 
                            codigoCosecha=codigo_cosecha, 
                            pesoNeto=peso_neto_carga, 
                            cuitTransportista=cuit_transportista,
                            cantHoras=cant_horas,
                            patente=patente_vehiculo, 
                            kmRecorridos=km_recorridos,
                            )))['response']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarCTGResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_ctg = datos.get('datosSolicitarCTG')
            if datos_ctg:
                self.NumeroCTG = str(datos_ctg['ctg'])
                self.FechaHora = str(datos_ctg['fechaEmision'])
                self.VigenciaDesde = str(datos_ctg['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_ctg['fechaVigenciaHasta'])
                self.TarifaReferencia = str(datos_ctg.get('tarifaReferencia'))
            self.__analizar_controles(datos)
        return self.NumeroCTG or 0
    
    @inicializar_y_capturar_excepciones
    def SolicitarCTGDatoPendiente(self, numero_carta_de_porte, cant_horas, 
        patente_vehiculo, cuit_transportista):
        "Solicitud que permite completar los datos faltantes de un Pre-CTG "
        "generado anteriormente a través de la operación solicitarCTGInicial"
        ret = self.client.solicitarCTGDatoPendiente(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosSolicitarCTGDatoPendiente=dict(
                            cartaPorte=numero_carta_de_porte, 
                            cuitTransportista=cuit_transportista,
                            cantHoras=cant_horas,
                            )))['response']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarCTGResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_ctg = datos.get('datosSolicitarCTG')
            if datos_ctg:
                self.NumeroCTG = str(datos_ctg['ctg'])
                self.FechaHora = str(datos_ctg['fechaEmision'])
                self.VigenciaDesde = str(datos_ctg['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_ctg['fechaVigenciaHasta'])
                self.TarifaReferencia = str(datos_ctg.get('tarifaReferencia'))
            self.__analizar_controles(datos)
        return self.NumeroCTG
        
    @inicializar_y_capturar_excepciones
    def ConfirmarArribo(self, numero_carta_de_porte, numero_ctg, 
                        cuit_transportista, peso_neto_carga, 
                        establecimiento, **kwargs):
        "Confirma arribo CTG"
        ret = self.client.confirmarArribo(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosConfirmarArribo=dict(
                            cartaPorte=numero_carta_de_porte, 
                            ctg=numero_ctg,
                            cuitTransportista=cuit_transportista,
                            cantKilosCartaPorte=peso_neto_carga,
                            establecimiento=establecimiento,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('datosResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['ctg'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoTransaccion = str(datos['codigoOperacion'])
            self.Observaciones = ""
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConfirmarDefinitivo(self, numero_carta_de_porte, numero_ctg, **kwargs):
        "Confirma arribo definitivo CTG"
        ret = self.client.confirmarDefinitivo(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosConfirmarDefinitivo=dict(
                            cartaPorte=numero_carta_de_porte, 
                            ctg=numero_ctg,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('datosResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['ctg'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoTransaccion = str(datos['codigoOperacion'])
            self.Observaciones = ""
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConsultarCTG(self, numero_carta_de_porte=None, numero_ctg=None, 
                     patente=None, cuit_solicitante=None, cuit_destino=None,
                     fecha_emision_desde=None, fecha_emision_hasta=None):
        "Operación que realiza consulta de CTGs según el criterio ingresado."
        ret = self.client.consultarCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        consultarCTGDatos=dict(
                            cartaPorte=numero_carta_de_porte, 
                            ctg=numero_ctg,
                            patente=patente,
                            cuitSolicitante=cuit_solicitante,
                            cuitDestino=cuit_destino,
                            fechaEmisionDesde=fecha_emision_desde,
                            fechaEmisionHasta=fecha_emision_hasta,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('arrayDatosConsultarCTG')
        if datos:
            self.DatosCTG = datos
            self.LeerDatosCTG(pop=False)
            return True
        else:
            self.DatosCTG = []
        return ''

    def LeerDatosCTG(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"
        
        if self.DatosCTG:
            # extraigo el primer item
            if pop:
                datos = self.DatosCTG.pop(0)
            else:
                datos = self.DatosCTG[0]
            datos_ctg = datos['datosConsultarCTG']
            self.CartaPorte = str(datos_ctg['cartaPorte'])
            self.NumeroCTG = str(datos_ctg['ctg'])
            self.Estado = unicode(datos_ctg['estado'])
            self.ImprimeConstancia = str(datos_ctg['imprimeConstancia'])
            self.FechaHora = str(datos_ctg['fechaSolicitud'])
            return self.NumeroCTG
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def ConsultarCTGExcel(self, numero_carta_de_porte=None, numero_ctg=None, 
                     patente=None, cuit_solicitante=None, cuit_destino=None,
                     fecha_emision_desde=None, fecha_emision_hasta=None,
                     archivo="planilla.xls"):
        "Operación que realiza consulta de CTGs, graba una planilla xls"
        ret = self.client.consultarCTGExcel(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        consultarCTGDatos=dict(
                            cartaPorte=numero_carta_de_porte, 
                            ctg=numero_ctg,
                            patente=patente,
                            cuitSolicitante=cuit_solicitante,
                            cuitDestino=cuit_destino,
                            fechaEmisionDesde=fecha_emision_desde,
                            fechaEmisionHasta=fecha_emision_hasta,
                            )))['response']
        self.__analizar_errores(ret)
        datos = base64.b64decode(ret.get('archivo', ""))
        f = open(archivo, "wb")
        f.write(datos)
        f.close()
        return True
        
    @inicializar_y_capturar_excepciones
    def ConsultarDetalleCTG(self, numero_ctg=None):
        "Operación mostrar este detalle de la  solicitud de CTG seleccionada."
        ret = self.client.consultarDetalleCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        ctg=numero_ctg, 
                        ))['response']
        self.__analizar_errores(ret)
        datos = ret.get('consultarDetalleCTGDatos')
        if datos:
            self.NumeroCTG = str(datos['ctg'])
            self.CartaPorte = str(datos['cartaPorte'])
            self.Estado = unicode(datos['estado'])
            self.FechaHora = str(datos['fechaEmision'])
            self.VigenciaDesde = str(datos['fechaVigenciaDesde'])
            self.VigenciaHasta = str(datos['fechaVigenciaHasta'])
            self.TarifaReferencia = str(datos['tarifaReferencia'])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarConstanciaCTGPDF(self, numero_ctg=None, 
                                        archivo="constancia.pdf"):
        "Operación Consultar Constancia de CTG en PDF"
        ret = self.client.consultarConstanciaCTGPDF(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        ctg=numero_ctg, 
                        ))['response']
        self.__analizar_errores(ret)
        datos = base64.b64decode(ret.get('archivo', ""))
        f = open(archivo, "wb")
        f.write(datos)
        f.close()
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarProvincias(self, sep="||"):
        ret = self.client.consultarProvincias(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['consultarProvinciasResponse']
        self.__analizar_errores(ret)
        array = ret.get('arrayProvincias', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['provincia']['codigo'], 
                     it['provincia']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarLocalidadesPorProvincia(self, codigo_provincia, sep="||"):
        ret = self.client.consultarLocalidadesPorProvincia(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        codigoProvincia=codigo_provincia,
                        ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayLocalidades', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['localidad']['codigo'], 
                     it['localidad']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarEstablecimientos(self, sep="||"):
        ret = self.client.consultarEstablecimientos(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayEstablecimientos', [])
        return [("%s" % 
                    (it['establecimiento'],)) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarEspecies(self, sep="||"):
        ret = self.client.consultarEspecies(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayEspecies', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['especie']['codigo'], 
                     it['especie']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarCosechas(self, sep="||"):
        ret = self.client.consultarCosechas(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayCosechas', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['cosecha']['codigo'], 
                     it['cosecha']['descripcion']) 
               for it in array]


def leer_archivo(nombre_archivo):
    archivo = open(nombre_archivo, "r")
    items = []
    ext = os.path.splitext(nombre_archivo)[1]
    if ext == '.csv':
        csv_reader = csv.reader(open(ENTRADA), dialect='excel', delimiter=";")
        for row in csv_reader:
            items.append(row)
        cols = [str(it).strip() for it in items[0]]
        # armar diccionario por cada linea
        items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]
        return cols, items
    elif ext == '.json':
        items = json.load(archivo)
    elif ext == '.dbf':
        dic = {}
        formatos = [('Encabezado', ENCABEZADO, dic), ]
        leer_dbf(formatos, conf_dbf)
        items = [dic]
    elif ext == '.txt':
        dic = {}
        for linea in archivo:
            if str(linea[0])=='0':
                dic.update(leer(linea, ENCABEZADO))
            else:
                print "Tipo de registro incorrecto:", linea[0]
        items.append(dic)
    else:
        raise RuntimeError("Extension de archivo desconocida: %s" % ext)
    archivo.close()
    cols = [k[0] for k in ENCABEZADO]
    return cols, items


def escribir_archivo(cols, items, nombre_archivo, agrega=False):
    archivo = open(nombre_archivo, agrega and "a" or "w")
    ext = os.path.splitext(nombre_archivo)[1]
    if ext == '.csv':
        csv_writer = csv.writer(archivo, dialect='excel', delimiter=";")
        csv_writer.writerows([cols])
        csv_writer.writerows([[item[k] for k in cols] for item in items])
    elif ext == '.json':
        json.dump(items, archivo, sort_keys=True, indent=4)
    elif ext == '.dbf':
        formatos = [('Encabezado', ENCABEZADO, items), ]
        guardar_dbf(formatos, True, conf_dbf)
    elif ext == '.txt':
        for dic in items:
            dic['tipo_reg'] = 0
            archivo.write(escribir(dic, ENCABEZADO))
    else:
        raise RuntimeError("Extension de archivo desconocida: %s" % ext)
    archivo.close()
    


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSCTG11.InstallDir = get_install_dir()


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)
    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in [('Encabezado', ENCABEZADO), ]:
            comienzo = 1
            print "=== %s ===" % msg
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                    clave, comienzo, longitud, tipo, dec)
                comienzo += longitud
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCTG11)
        sys.exit(0)

    import csv
    from ConfigParser import SafeConfigParser

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                break
            print "Usando configuración:", arg
            CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSCTG','CUIT')
        ENTRADA = config.get('WSCTG','ENTRADA')
        SALIDA = config.get('WSCTG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = None
        if config.has_option('WSCTG','URL') and not HOMO:
            wsctg_url = config.get('WSCTG','URL')
        else:
            wsctg_url = WSDL

        if config.has_section('DBF'):
            conf_dbf = dict(config.items('DBF'))
            if DEBUG: print "conf_dbf", conf_dbf
        else:
            conf_dbf = {}

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "wsctg_url:", wsctg_url

        # obteniendo el TA
        from wsaa import WSAA
        ta = WSAA().Autenticar("wsctg", CERT, PRIVATEKEY, wsaa_url)

        # cliente soap del web service
        wsctg = WSCTG11()
        wsctg.Conectar(wsdl=wsctg_url)
        wsctg.SetTicketAcceso(ta)
        wsctg.Cuit = CUIT
        
        if '--dummy' in sys.argv:
            ret = wsctg.Dummy()
            print "AppServerStatus", wsctg.AppServerStatus
            print "DbServerStatus", wsctg.DbServerStatus
            print "AuthServerStatus", wsctg.AuthServerStatus
            sys.exit(0)

        if '--anular' in sys.argv:
            i = sys.argv.index("--anular")
            ##print wsctg.client.help("anularCTG")
            if i + 2 > len(sys.argv) or sys.argv[i + 1].startswith("--"):
                carta_porte = raw_input("Ingrese Carta de Porte: ")
                ctg = raw_input("Ingrese CTG: ")
            else:
                carta_porte = sys.argv[i + 1]
                ctg = sys.argv[i + 2]
            ret = wsctg.AnularCTG(carta_porte, ctg)
            print "Carta Porte", wsctg.CartaPorte
            print "Numero CTG", wsctg.NumeroCTG
            print "Fecha y Hora", wsctg.FechaHora
            print "Codigo Anulacion de CTG", wsctg.CodigoOperacion
            print "Errores:", wsctg.Errores
            sys.exit(0)

        if '--rechazar' in sys.argv:
            i = sys.argv.index("--rechazar")
            ##print wsctg.client.help("rechazarCTG")
            if i + 3 > len(sys.argv) or sys.argv[i + 1].startswith("--"):
                carta_porte = raw_input("Ingrese Carta de Porte: ")
                ctg = raw_input("Ingrese CTG: ")
                motivo = raw_input("Motivo: ")
            else:
                carta_porte = sys.argv[i + 1]
                ctg = sys.argv[i + 2]
                motivo = sys.argv[i + 3]
            ret = wsctg.RechazarCTG(carta_porte, ctg, motivo)
            print "Carta Porte", wsctg.CartaPorte
            print "Numero CTG", wsctg.NumeroCTG
            print "Fecha y Hora", wsctg.FechaHora
            print "Codigo Anulacion de CTG", wsctg.CodigoOperacion
            print "Errores:", wsctg.Errores
            sys.exit(0)


        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            ret = wsctg.ConsultarProvincias()
            print "\n".join(ret)
                    
        if '--localidades' in sys.argv:    
            ret = wsctg.ConsultarLocalidadesPorProvincia(16)
            print "\n".join(ret)

        if '--especies' in sys.argv:    
            ret = wsctg.ConsultarEspecies()
            print "\n".join(ret)

        if '--cosechas' in sys.argv:    
            ret = wsctg.ConsultarCosechas()
            print "\n".join(ret)

        if '--establecimientos' in sys.argv:    
            ret = wsctg.ConsultarEstablecimientos()
            print "\n".join(ret)


        if '--prueba' in sys.argv or '--formato' in sys.argv:
            prueba = dict(numero_carta_de_porte=512345679, codigo_especie=23,
                cuit_canjeador=0, #30660685908, 
                cuit_destino=20061341677, cuit_destinatario=20267565393, 
                codigo_localidad_origen=3058, codigo_localidad_destino=3059, 
                codigo_cosecha='1314', peso_neto_carga=1000, 
                km_recorridos=1234,
                ##numero_ctg="43816783", transaccion='10000001681', 
                observaciones='', establecimiento=1,
            )
            parcial = dict(
                    cant_horas=1, 
                    patente_vehiculo='CZO985', cuit_transportista=20234455967,
                    )
            if not '--parcial' in sys.argv:
                prueba.update(parcial)
            
            escribir_archivo(prueba.keys(), [prueba], ENTRADA)
            
        cols, items = leer_archivo(ENTRADA)
        ctg = None

        if '--solicitar' in sys.argv:
            wsctg.LanzarExcepciones = True
            for it in items:
                print "solicitando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                ctg = wsctg.SolicitarCTGInicial(**it)
                print "numero CTG: ", ctg
                print "Observiacion: ", wsctg.Observaciones
                print "Carta Porte", wsctg.CartaPorte
                print "Numero CTG", wsctg.NumeroCTG
                print "Fecha y Hora", wsctg.FechaHora
                print "Vigencia Desde", wsctg.VigenciaDesde
                print "Vigencia Hasta", wsctg.VigenciaHasta
                print "Tarifa Referencia: ", wsctg.TarifaReferencia
                print "Errores:", wsctg.Errores
                print "Controles:", wsctg.Controles
                it['numero_ctg'] = wsctg.NumeroCTG
                it['tarifa_referencia'] = wsctg.TarifaReferencia
                it['observaciones'] = wsctg.Observaciones
                it['fecha_hora'] = wsctg.FechaHora
                it['vigencia_desde'] = wsctg.VigenciaDesde
                it['vigencia_hasta'] = wsctg.VigenciaHasta
                it['errores'] = '|'.join(wsctg.Errores)
                it['controles'] = '|'.join(wsctg.Controles)

        if '--parcial' in sys.argv:
            wsctg.LanzarExcepciones = True
            for it in items:
                print "solicitando dato pendiente...", ' '.join(['%s=%s' % (k,v) for k,v in parcial.items()])
                ctg = wsctg.SolicitarCTGDatoPendiente(
                    numero_carta_de_porte=wsctg.CartaPorte,
                    **parcial)
                print "numero CTG: ", ctg
                print "Observiacion: ", wsctg.Observaciones
                print "Carta Porte", wsctg.CartaPorte
                print "Numero CTG", wsctg.NumeroCTG
                print "Fecha y Hora", wsctg.FechaHora
                print "Vigencia Desde", wsctg.VigenciaDesde
                print "Vigencia Hasta", wsctg.VigenciaHasta
                print "Tarifa Referencia: ", wsctg.TarifaReferencia
                print "Errores:", wsctg.Errores
                print "Controles:", wsctg.Controles
                it['numero_ctg'] = wsctg.NumeroCTG
                it['tarifa_referencia'] = wsctg.TarifaReferencia
                it['errores'] = '|'.join(wsctg.Errores)
                it['controles'] = '|'.join(wsctg.Controles)

        if '--confirmar_arribo' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                transaccion = wsctg.ConfirmarArribo(**it)
                print "transaccion: %s" % (transaccion, )
                print "Fecha y Hora", wsctg.FechaHora
                print "Errores:", wsctg.Errores
                it['transaccion'] = transaccion
                it['errores'] = '|'.join(wsctg.Errores)
                it['controles'] = '|'.join(wsctg.Controles)
                
        if '--confirmar_definitivo' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                transaccion = wsctg.ConfirmarDefinitivo(**it)
                print "transaccion: %s" % (transaccion, )
                print "Fecha y Hora", wsctg.FechaHora
                print "Errores:", wsctg.Errores
                it['transaccion'] = transaccion
                it['errores'] = '|'.join(wsctg.Errores)
                it['controles'] = '|'.join(wsctg.Errores)
                
        if '--consultar_detalle' in sys.argv:
            i = sys.argv.index("--consultar_detalle")
            if len(sys.argv) > i + 1 and not sys.argv[i+1].startswith("--"):
                ctg = int(sys.argv[i+1])
            elif not ctg:
                ctg = int(raw_input("Numero de CTG: ") or '0') or 73714620

            wsctg.LanzarExcepciones = True
            for i, it in enumerate(items):
                print "consultando detalle...", ctg
                ok = wsctg.ConsultarDetalleCTG(ctg)
                print "Numero CTG: ", wsctg.NumeroCTG
                print "Tarifa Referencia: ", wsctg.TarifaReferencia
                print "Observiacion: ", wsctg.Observaciones
                print "Carta Porte", wsctg.CartaPorte
                print "Numero CTG", wsctg.NumeroCTG
                print "Fecha y Hora", wsctg.FechaHora
                print "Vigencia Desde", wsctg.VigenciaDesde
                print "Vigencia Hasta", wsctg.VigenciaHasta
                print "Errores:", wsctg.Errores
                print "Controles:", wsctg.Controles
                it['numero_ctg'] = wsctg.NumeroCTG
                it['observaciones'] = wsctg.Observaciones
                it['fecha_hora'] = wsctg.FechaHora
                it['vigencia_desde'] = wsctg.VigenciaDesde
                it['vigencia_hasta'] = wsctg.VigenciaHasta
                wsctg.AnalizarXml("XmlResponse")
                for k, ki in {'ctg': 'numero_ctg', 'solicitante': '', 
                          'estado': 'estado', 
                          'especie': '', ##'codigo_especie', no devuelve codigo! 
                          'cosecha': '', ##'codigo_cosecha', no devuelve codigo!
                          'cuitCanjeador': 'cuit_canjeador', 
                          'cuitDestino': 'cuit_destino', 
                          'cuitDestinatario': 'cuit_destinatario', 
                          'cuitTransportista': 'cuit_transportista', 
                          'establecimiento': 'establecimiento', 
                          'localidadOrigen': 'localidad_origen', 
                          'localidadDestino': 'localidad_destino',
                          'cantidadHoras': 'cantidad_horas', 
                          'patenteVehiculo': 'patente_vehiculo', 
                          'pesoNetoCarga': 'peso_neto_carga',
                          'kmRecorridos': 'km_recorridos', 
                          'tarifaReferencia': 'tarifa_referencia', }.items():
                    v = wsctg.ObtenerTagXml('consultarDetalleCTGDatos', k)
                    print k, v
                    if ki.startswith("cuit") and v:
                        v = v[:11]
                    it[ki] = v
    
        escribir_archivo(cols, items, SALIDA)
        
        if "--consultar" in sys.argv:
            wsctg.LanzarExcepciones = True
            wsctg.ConsultarCTG(fecha_emision_desde="01/04/2012")
            print "Numero CTG - Carta de Porte - Imprime Constancia - Estado"
            while wsctg.LeerDatosCTG():
                print wsctg.NumeroCTG, wsctg.CartaPorte,
                print wsctg.ImprimeConstancia, wsctg.Estado, wsctg.FechaHora

        if '--consultar_excel' in sys.argv:
            archivo = raw_input("Archivo a generar (planilla.xls): ") or \
                        'planilla.xls'
            wsctg.LanzarExcepciones = True
            ok = wsctg.ConsultarCTGExcel(fecha_emision_desde="01/04/2012",
                                         archivo=archivo)
            print "Errores:", wsctg.Errores

        if '--consultar_constancia_pdf' in sys.argv:
            i = sys.argv.index("--consultar_constancia_pdf")
            if len(sys.argv) > i + 2 and not sys.argv[i+1].startswith("--"):
                ctg = int(sys.argv[i+1])
                archivo = sys.argv[i+2]
            elif not ctg:
                ctg = int(raw_input("Numero de CTG: ") or '0') or 83139794
                archivo = raw_input("Archivo a generar (constancia.pdf): ") or \
                            'constancia.pdf'

            wsctg.LanzarExcepciones = True
            ok = wsctg.ConsultarConstanciaCTGPDF(ctg, archivo)
            print "Errores:", wsctg.Errores

            
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        ex = utils.exception_info()
        print ex
        if DEBUG:
            raise
        sys.exit(5)
