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

"""Módulo para obtener código de operación electrónico (COE) para 
Liquidación Primaria Electrónica de Granos del web service WSLPG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.04d"

LICENCIA = """
wslpg.py: Interfaz para generar Código de Operación Electrónica para
Liquidación Primaria de Granos (LpgService)
Copyright (C) 2013 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo respetando la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA="""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una liquidación de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)

  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación Primaria de Granos (liquidacionAutorizar)
  --ajustar: Ajustar Liquidación Primaria de Granos (liquidacionAjustar)
  --anular: Anular una Liquidación Primaria de Granos (liquidacionAnular)
  --consultar: Consulta una liquidación (parámetros: nro de orden y COE)
  --ult: Consulta el último número de orden registrado en AFIP 
         (liquidacionUltimoNroOrdenConsultar)

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --tipograno: obtiene el listado de los tipos de granos disponibles
  --campanias: obtiene el listado de las campañas 
  --gradoref: obtiene el listado de los grados de referencias
  --certdeposito: obtiene el listado de los tipos de certificados de depósito
  --deducciones: obtiene el listado de los tipos de deducciones
  --retenciones: obtiene el listado de los tipos de retenciones
  --puertos: obtiene el listado de los puertos habilitados
  --actividades: obtiene el listado de las actividades habilitados
  --operaciones: obtiene el listado de las operaciones para el representado


Ver wslpg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time
from php import date
import traceback
import pprint
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

from rece1 import leer, escribir  # esto debería estar en un módulo separado

WSDL = "https://fwshomo.afip.gov.ar/wslpg/LpgService?wsdl"
#WSDL = "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl"
#WSDL = "file:wslpg.wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslpg.ini"
HOMO = True

# definición del formato del archivo de intercambio:
N = 'Numerico'
A = 'Alfanumerico'
I = 'Importe'

ENCABEZADO = [
    ('tipo_reg', 1, A), # 0: encabezado
    ('nro_orden', 18, N), 
    ('cuit_comprador', 11, N),
    ('nro_act_comprador', 5, N),
    ('nro_ing_bruto_comprador', 15, N), 
    ('cod_tipo_operacion', 2, N), 
    ('es_liquidacion_propia', 1, A),  # S o N
    ('es_canje', 1, A),  # S o N
    ('cod_puerto', 4, N), 
    ('des_puerto_localidad', 240, A), 
    ('cod_grano', 3, N), 
    ('cuit_vendedor', 11, N), 
    ('nro_ing_bruto_vendedor', 15, N), 
    ('actua_corredor', 1, A),  # S o N
    ('liquida_corredor', 1, A),  # S o N
    ('cuit_corredor', 11, N), 
    ('nro_ing_bruto_corredor', 15, N), 
    ('comision_corredor', 5, I, 2), # 3.2
    ('fecha_precio_operacion', 10, A), # 26/02/2013
    ('precio_ref_tn', 8, I, 3), # 4.3
    ('cod_grado_ref', 2, A),
    ('cod_grado_ent', 2, A),
    ('factor_ent', 6, I, 3), # 3.3
    ('precio_flete_tn', 7, I, 2), # 5.2
    ('cont_proteico', 6, I, 3), # 3.3
    ('alic_iva_operacion', 5, I, 2), # 3.2
    ('campania_ppal', 4, N),
    ('cod_localidad_procedencia', 6, N), 
    ('datos_adicionales', 200, A),
    
    ('coe', 12, N),
    ('coe_ajustado', 12, N),
    ('estado', 2, A),
    
    ('total_deduccion', 17, I, 2), # 17.2
    ('total_retencion', 17, I, 2), # 17.2
    ('total_retencion_afip', 17, I, 2), # 17.2
    ('total_otras_retenciones', 17, I, 2), # 17.2
    ('total_neto_a_pagar', 17, I, 2), # 17.2
    ('total_iva_rg_2300_07', 17, I, 2), # 17.2
    ('total_pago_segun_condicion', 17, I, 2), # 17.2
    
    ('fecha_liquidacion', 10, A), 
    ('nro_op_comercial', 10, N), 
    ('precio_operacion', 17, I, 3), # 17.3
    ('subtotal', 17, I, 2), # 17.2
    ('importe_iva', 17, I, 2), # 17.2
    ('operacion_con_iva', 17, I, 2), # 17.2
    ('total_peso_neto', 8, N), # 17.2

    # Campos WSLPGv1.1:
    ('pto_emision', 4, N), 
    ('cod_prov_procedencia', 2, N),
    ('peso_neto_sin_certificado', 8, N),
        
    ]

CERTIFICADO = [
    ('tipo_reg', 1, A), # 1: Certificado
    ('tipo_certificado_deposito', 2, N), 
    ('nro_certificado_deposito', 12, N), 
    ('peso_neto', 8, N), 
    ('cod_localidad_procedencia', 6, N), 
    ('cod_prov_procedencia', 2, N),
    ('reservado', 2, N),
    ('campania', 4, N),
    ('fecha_cierre', 10, A),
    ]
    
RETENCION = [
    ('tipo_reg', 1, A), # 2: Retencion
    ('codigo_concepto', 2, A), 
    ('detalle_aclaratorio', 30, A),
    ('base_calculo', 10, I, 2),  # 8.2
    ('alicuota', 6, I, 2),  # 3.2
    ('nro_certificado_retencion', 14, N), 
    ('fecha_certificado_retencion', 10, A),
    ('importe_certificado_retencion', 17, I, 2), # 17.2
    ('importe_retencion', 17, I, 2), # 17.2
    ]

DEDUCCION = [
    ('tipo_reg', 1, A), # 3: Deducción
    ('codigo_concepto', 2, A), 
    ('detalle_aclaratorio', 30, A),
    ('dias_almacenaje', 4, N),
    ('precio_pkg_diario', 6, I, 3), # 3.3
    ('comision_gastos_adm', 5, I, 2), # 3.2
    ('base_calculo', 10, I, 2),  # 8.2
    ('alicuota', 6, I, 2),  # 3.2
    ('importe_iva', 17, I, 2), # 17.2
    ('importe_deduccion', 17, I, 2), # 17.2
    ]

EVENTO = [
    ('tipo_reg', 1, A), # E: Evento
    ('codigo', 4, A), 
    ('descripcion', 250, A), 
    ]
    
ERROR = [
    ('tipo_reg', 1, A), # R: Error
    ('codigo', 4, A), 
    ('descripcion', 250, A), 
    ]


def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.COE = self.COEAjustado = ""
            self.Excepcion = self.Traceback = ""
            self.ErrMsg = self.ErrCode = ""
            self.Errores = []
            self.Estado = self.Resultado = self.NroOrden = ''
            self.TotalDeduccion = ""
            self.TotalRetencion = ""
            self.TotalRetencionAfip = ""
            self.TotalOtrasRetenciones = ""
            self.TotalNetoAPagar = ""
            self.TotalIvaRg2300_07 = ""
            self.TotalPagoSegunCondicion = ""
            # actualizo los parámetros
            kwargs.update(self.params)
            self.params = {}
            # llamo a la función
            func(self, *args, **kwargs)
            # limpio los parámetros
            return True
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
            else:
                return False
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            else:
                return False
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSLPG:
    "Interfaz para el WebService de Liquidación Primaria de Granos"    
    _public_methods_ = ['Conectar', 'Dummy', 'LoadTestXML',
                        'AutorizarLiquidacion', 'AjustarLiquidacion',
                        'AnularLiquidacion',
                        'CrearLiquidacion',  
                        'AgregarCertificado', 'AgregarRetencion', 
                        'AgregarDeduccion',
                        'ConsultarLiquidacion', 'ConsultarUltNroOrden',
                        'ConsultarCampanias',
                        'ConsultarTipoGrano',
                        'ConsultarGradoEntregadoXTipoGrano',
                        'ConsultarCodigoGradoReferencia',
                        'ConsultarTipoCertificadoDeposito',
                        'ConsultarTipoDeduccion',
                        'ConsultarTipoRetencion',
                        'ConsultarPuerto',
                        'ConsultarTipoActividad',
                        'ConsultarProvincias',
                        'ConsultarLocalidadesPorProvincia',
                        'ConsultarTiposOperacion',
                        'AnalizarXml', 'ObtenerTagXml',
                        'SetParametro', 'GetParametro',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'InstallDir',
        'COE', 'COEAjustado', 'Estado', 'Resultado', 'NroOrden',
        'TotalDeduccion', 'TotalRetencion', 'TotalRetencionAfip', 
        'TotalOtrasRetenciones', 'TotalNetoAPagar', 'TotalPagoSegunCondicion',
        'TotalIvaRg2300_07'
        ]
    _reg_progid_ = "WSLPG"
    _reg_clsid_ = "{9D21C513-21A6-413C-8592-047357692608}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.LanzarExcepciones = False
        self.InstallDir = INSTALL_DIR
        self.ErrCode = self.ErrMsg = ''
        self.Errores = self.errores = []
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.COE = ''
        self.Estado = self.Resultado = self.NroOrden = ''
        self.params = {}

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = WSDL
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        proxy_dict = parse_proxy(proxy)
        self.client = SoapClient(url,
            wsdl=url, cache=cache,
            trace='--trace' in sys.argv, 
            ns='wslpg', soap_ns='soapenv',
            exceptions=True, proxy=proxy_dict)
        return True

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if 'errores' in ret:
            errores.extend(ret['errores'])
        if 'erroresFormato' in ret:
            errores.extend(ret['erroresFormato'])
        if errores:
            self.Errores = ["%(codigo)s: %(descripcion)s" % err['error'] 
                            for err in errores]
            self.errores = [
                {'codigo': err['error']['codigo'],
                 'descripcion': err['error']['descripcion'].replace("\n", "")} 
                             for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['return']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def CrearLiquidacion(self, nro_orden=None, cuit_comprador=None, 
               nro_act_comprador=None, nro_ing_bruto_comprador=None,
               cod_tipo_operacion=None,
               es_liquidacion_propia=None, es_canje=None,
               cod_puerto=None, des_puerto_localidad=None, cod_grano=None,
               cuit_vendedor=None, nro_ing_bruto_vendedor=None,
               actua_corredor=None, liquida_corredor=None, cuit_corredor=None,
               comision_corredor=None, nro_ing_bruto_corredor=None,
               fecha_precio_operacion=None,
               precio_ref_tn=None, cod_grado_ref=None, cod_grado_ent=None,
               factor_ent=None, precio_flete_tn=None, cont_proteico=None,
               alic_iva_operacion=None, campania_ppal=None,
               cod_localidad_procedencia=None,
               datos_adicionales=None, pto_emision=1, cod_prov_procedencia=None, 
               peso_neto_sin_certificado=None,
               **kwargs
               ):
        self.liquidacion = dict(
                            ptoEmision=pto_emision,
                            nroOrden=nro_orden,
                            cuitComprador=cuit_comprador,
                            nroActComprador=nro_act_comprador,
                            nroIngBrutoComprador=nro_ing_bruto_comprador,
                            codTipoOperacion=cod_tipo_operacion,
                            esLiquidacionPropia=es_liquidacion_propia,
                            esCanje=es_canje,
                            codPuerto=cod_puerto,
                            desPuertoLocalidad=des_puerto_localidad,
                            codGrano=cod_grano,
                            cuitVendedor=cuit_vendedor,
                            nroIngBrutoVendedor=nro_ing_bruto_vendedor,
                            actuaCorredor=actua_corredor,
                            liquidaCorredor=liquida_corredor,
                            cuitCorredor=cuit_corredor,
                            comisionCorredor=comision_corredor,
                            nroIngBrutoCorredor=nro_ing_bruto_corredor,
                            fechaPrecioOperacion=fecha_precio_operacion,
                            precioRefTn=precio_ref_tn,
                            codGradoRef=cod_grado_ref,
                            codGradoEnt=cod_grado_ent,
                            factorEnt=factor_ent,
                            precioFleteTn=precio_flete_tn,
                            contProteico=cont_proteico,
                            alicIvaOperacion=alic_iva_operacion,
                            campaniaPPal=campania_ppal,
                            codLocalidadProcedencia=cod_localidad_procedencia,
                            codProvProcedencia=cod_prov_procedencia,
                            datosAdicionales=datos_adicionales,
                            pesoNetoSinCertificado=peso_neto_sin_certificado,
                            certificados=[],
            )
        self.retenciones = []
        self.deducciones = []

    @inicializar_y_capturar_excepciones
    def AgregarCertificado(self, tipo_certificado_deposito=None,
                           nro_certificado_deposito=None,
                           peso_neto=None,
                           cod_localidad_procedencia=None,
                           cod_prov_procedencia=None,
                           campania=None,
                           fecha_cierre=None, **kwargs):
        "Agrego el certificado a la liquidación"
        
        self.liquidacion['certificados'].append(
                    dict(certificado=dict(
                        tipoCertificadoDeposito=tipo_certificado_deposito,
                        nroCertificadoDeposito=nro_certificado_deposito,
                        pesoNeto=peso_neto,
                        codLocalidadProcedencia=cod_localidad_procedencia,
                        codProvProcedencia=cod_prov_procedencia,
                        campania=campania,
                        fechaCierre=fecha_cierre,
                      )))

    @inicializar_y_capturar_excepciones
    def AgregarRetencion(self, codigo_concepto, detalle_aclaratorio, 
                               base_calculo, alicuota, **kwargs):
        "Agrega la información referente a las retenciones de la liquidación"
        self.retenciones.append(dict(
                                    retencion=dict(
                                        codigoConcepto=codigo_concepto,
                                        detalleAclaratorio=detalle_aclaratorio,
                                        baseCalculo=base_calculo,
                                        alicuota=alicuota,
                                    ))
                            )

    @inicializar_y_capturar_excepciones
    def AgregarDeduccion(self, codigo_concepto=None, detalle_aclaratorio=None,
                               dias_almacenaje=None, precio_pkg_diario=None,
                               comision_gastos_adm=None, base_calculo=None,
                               alicuota=None, **kwargs):
        "Agrega la información referente a las deducciones de la liquidación."
        # limpiar campo según validación (comision_gastos_adm debe ser >=0.01)
        if comision_gastos_adm is not None and float(comision_gastos_adm) == 0:
            comision_gastos_adm = None
        self.deducciones.append(dict(
                                    deduccion=dict(
                                        codigoConcepto=codigo_concepto,
                                        detalleAclaratorio=detalle_aclaratorio,
                                        diasAlmacenaje=dias_almacenaje,
                                        precioPKGdiario=precio_pkg_diario,
                                        comisionGastosAdm=comision_gastos_adm,
                                        baseCalculo=base_calculo,
                                        alicuotaIva=alicuota
                                    ))
                            )

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Autorizar Liquidación Primaria Electrónica de Granos"
        
        # limpio los elementos que no correspondan por estar vacios:
        if not self.liquidacion['certificados']:
            del self.liquidacion['certificados']
        if not self.retenciones:
            self.retenciones = None
        if not self.deducciones:
            self.deducciones = None
        
        # llamo al webservice:
        ret = self.client.liquidacionAutorizar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        liquidacion=self.liquidacion,
                        retenciones=self.retenciones,
                        deducciones=self.deducciones,
                        )

        # analizo la respusta
        ret = ret['liqReturn']
        self.__analizar_errores(ret)
        if 'autorizacion' in ret:
            aut = ret['autorizacion']
            self.AnalizarLiquidacion(aut, self.liquidacion)

    def AnalizarLiquidacion(self, aut, liq=None):
        "Método interno para analizar la respuesta de AFIP"
        # proceso los datos básicos de la liquidación (devuelto por consultar):
        if liq:
            self.params = dict(
                        pto_emision=liq.get('ptoEmision'),
                        nro_orden=liq.get('nroOrden'),
                        cuit_comprador=liq.get('cuitComprador'),
                        nro_act_comprador=liq.get('nroActComprador'),
                        nro_ing_bruto_comprador=liq.get('nroIngBrutoComprador'),
                        cod_tipo_operacion=liq.get('codTipoOperacion'),
                        es_liquidacion_propia=liq.get('esLiquidacionPropia'),
                        es_canje=liq.get('esCanje'),
                        cod_puerto=liq.get('codPuerto'),
                        des_puerto_localidad=liq.get('desPuertoLocalidad'),
                        cod_grano=liq.get('codGrano'),
                        cuit_vendedor=liq.get('cuitVendedor'),
                        nro_ing_bruto_vendedor=liq.get('nroIngBrutoVendedor'),
                        actua_corredor=liq.get('actuaCorredor'),
                        liquida_corredor=liq.get('liquidaCorredor'),
                        cuit_corredor=liq.get('cuitCorredor'),
                        comision_corredor=liq.get('comisionCorredor'),
                        nro_ing_bruto_corredor=liq.get('nroIngBrutoCorredor'),
                        fecha_precio_operacion=liq.get('fechaPrecioOperacion'),
                        precio_ref_tn=liq.get('precioRefTn'),
                        cod_grado_ref=liq.get('codGradoRef'),
                        cod_grado_ent=liq.get('codGradoEnt'),
                        factor_ent=liq.get('factorEnt'),
                        precio_flete_tn=liq.get('precioFleteTn'),
                        cont_proteico=liq.get('contProteico'),
                        alic_iva_operacion=liq.get('alicIvaOperacion'),
                        campania_ppal=liq.get('campaniaPPal'),
                        cod_localidad_procedencia=liq.get('codLocalidadProcedencia'),
                        cod_prov_procedencia=liq.get('codProvProcedencia'),
                        datos_adicionales=liq.get('datosAdicionales'),
                        peso_neto=liq.get('pesoNetoSinCertificado'),
                        certificados=[],
                    )
            if 'certificados' in liq:
                for c in liq['certificados']:
                    cert = c['certificado']
                    self.params['certificados'].append(dict(
                        tipo_certificado_deposito=cert['tipoCertificadoDeposito'],
                        nro_certificado_deposito=cert['nroCertificadoDeposito'],
                        peso_neto=cert['pesoNeto'],
                        cod_localidad_procedencia=cert['codLocalidadProcedencia'],
                        cod_prov_procedencia=cert['codProvProcedencia'],
                        campania=cert['campania'],
                        fechaCierre=cert['fechaCierre'],
                    ))
        # proceso la respuesta de autorizar, ajustar (y consultar):
        if aut:
            self.TotalDeduccion = aut['totalDeduccion']
            self.TotalRetencion = aut['totalRetencion']
            self.TotalRetencionAfip = aut['totalRetencionAfip']
            self.TotalOtrasRetenciones = aut['totalOtrasRetenciones']
            self.TotalNetoAPagar = aut['totalNetoAPagar']
            self.TotalIvaRg2300_07 = aut['totalIvaRg2300_07']
            self.TotalPagoSegunCondicion = aut['totalPagoSegunCondicion']
            self.COE = str(aut['coe'])
            self.COEAjustado = aut.get('coeAjustado')
            self.Estado = aut['estado']

            # actualizo parámetros de salida:
            self.params['coe'] = self.COE
            self.params['coe_ajustado'] = self.COE
            self.params['estado'] = self.Estado
            self.params['total_deduccion'] = self.TotalDeduccion
            self.params['total_retencion'] = self.TotalRetencion
            self.params['total_retencion_afip'] = self.TotalRetencionAfip
            self.params['total_otras_retenciones'] = self.TotalOtrasRetenciones
            self.params['total_neto_a_pagar'] = self.TotalNetoAPagar
            self.params['total_iva_rg_2300_07'] = self.TotalIvaRg2300_07
            self.params['total_pago_segun_condicion'] = self.TotalPagoSegunCondicion
            self.params['errores'] = self.errores

            # datos adicionales:
            self.params['nro_orden'] = aut.get('nroOrden')
            fecha = aut.get('fechaLiquidacion')
            if fecha:
                fecha = fecha.strftime("%d/%m/%Y")
            self.params['fecha_liquidacion'] = fecha
            self.params['importe_iva'] = aut.get('importeIva')
            self.params['nro_op_comercial'] = aut.get('nroOpComercial')
            self.params['operacion_con_iva'] = aut.get('operacionConIva')
            self.params['precio_operacion'] = aut.get('precioOperacion')
            self.params['total_peso_neto'] = aut.get('totalPesoNeto')
            self.params['subtotal'] = aut.get('subTotal')
            self.params['retenciones'] = []
            self.params['deducciones'] = []
            for retret in aut.get("retenciones", []):
                retret = retret['retencionReturn']
                self.params['retenciones'].append({
                    'importe_retencion': retret['importeRetencion'],
                    'alicuota': retret['retencion'].get('alicuota'),
                    'base_calculo': retret['retencion'].get('baseCalculo'),
                    'codigo_concepto': retret['retencion'].get('codigoConcepto'),
                    'detalle_aclaratorio': retret['retencion'].get('detalleAclaratorio', "").replace("\n", ""),
                    'importe_certificado_retencion': retret['retencion'].get('importeCertificadoRetencion'),
                    'nro_certificado_retencion': retret['retencion'].get('nroCertificadoRetencion'),
                    })
            for dedret in aut.get("deducciones", []):
                dedret = dedret['deduccionReturn']
                self.params['deducciones'].append({
                    'importe_deduccion': dedret['importeDeduccion'],
                    'importe_iva': dedret.get('importeIva'),
                     'alicuota_iva': dedret['deduccion'].get('alicuotaIva'),
                     'base_calculo': dedret['deduccion'].get('baseCalculo'),
                     'codigo_concepto': dedret['deduccion'].get('codigoConcepto'),
                     'detalle_aclaratorio': dedret['deduccion'].get('detalleAclaratorio', "").replace("\n", ""),
                     'dias_almacenaje': dedret['deduccion'].get('diasAlmacenaje'),
                     'precio_pkg_diario': dedret['deduccion'].get('precioPKGdiario'),
                     'comision_gastos_adm': dedret['deduccion'].get('comisionGastosAdm'),
                    })


    @inicializar_y_capturar_excepciones
    def AjustarLiquidacion(self, coe_ajustado=None, cod_tipo_ajuste=None, 
                                 total_peso_neto=None, precio_operacion=None,):
        "Ajustar Liquidación Primaria de Granos (tipo: 3 – Débito, 4 – Crédito)"
        ajuste = self.liquidacion.copy()
        # completo los datos del ajuste:
        ajuste['coeAjustado'] = coe_ajustado
        ajuste['codTipoAjuste'] = cod_tipo_ajuste
        ajuste['totalPesoNeto'] = total_peso_neto
        ajuste['precioOperacion'] = precio_operacion
        
        ret = self.client.liquidacionAjustar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        ajuste=ajuste,
                        deducciones=self.deducciones,
                        retenciones=self.retenciones,
                        )
        ret = ret['ajusteReturn']
        self.__analizar_errores(ret)
        if 'autorizacion' in ret:
            aut = ret['autorizacion']
            self.AnalizarLiquidacion(aut)

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(self, pto_emision=None, nro_orden=None, coe=None):
        "Consulta una liquidación por No de orden"
        if coe:
            ret = self.client.liquidacionXCoeConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        coe=coe,
                        )
        else:
            ret = self.client.liquidacionXNroOrdenConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        ptoEmision=pto_emision,
                        nroOrden=nro_orden,
                        )
        ret = ret['liqConsReturn']
        self.__analizar_errores(ret)
        if 'liquidacion' in ret:
            aut = ret['autorizacion']
            liq = ret['liquidacion']
            self.AnalizarLiquidacion(aut, liq)

    @inicializar_y_capturar_excepciones
    def ConsultarUltNroOrden(self, pto_emision=1):
        "Consulta el último No de orden registrado"
        ret = self.client.liquidacionUltimoNroOrdenConsultar(
                    auth={
                        'token': self.Token, 'sign': self.Sign,
                        'cuit': self.Cuit, },
                    ptoEmision=pto_emision,
                    )
        ret = ret['liqUltNroOrdenReturn']
        self.__analizar_errores(ret)
        self.NroOrden = ret['nroOrden']

    @inicializar_y_capturar_excepciones
    def LeerDatosLiquidacion(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"
        
        if self.DatosLiquidacion:
            # extraigo el primer item
            if pop:
                datos = self.DatosLiquidacion.pop(0)
            else:
                datos = self.DatosLiquidacion[0]
            datos_Liquidacion = datos['datosConsultarLiquidacion']
            self.COE = str(datos_Liquidacion['Liquidacion'])
            self.Estado = unicode(datos_Liquidacion['estado'])
            return self.COE
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def AnularLiquidacion(self, coe):
        "Anular liquidación activa"
        ret = self.client.liquidacionAnular(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        coe=coe,
                        )
        ret = ret['anulacionReturn']
        self.__analizar_errores(ret)
        self.Resultado = ret['resultado']
        return self.COE
        
    def ConsultarCampanias(self, sep="||"):
        ret = self.client.campaniasConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['campaniaReturn']
        self.__analizar_errores(ret)
        array = ret.get('campanias', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoGrano(self, sep="||"):
        ret = self.client.tipoGranoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoGranoReturn']
        self.__analizar_errores(ret)
        array = ret.get('granos', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarCodigoGradoReferencia(self, sep="||"):
        "Consulta de Grados según Grano."
        ret = self.client.codigoGradoReferenciaConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['gradoRefReturn']
        self.__analizar_errores(ret)
        array = ret.get('gradosRef', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarGradoEntregadoXTipoGrano(self, cod_grano, sep="||"):
        "Consulta de Grado y Valor según Grano Entregado."
        ret = self.client.codigoGradoEntregadoXTipoGranoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        codGrano=cod_grano,
                            )['gradoEntReturn']
        self.__analizar_errores(ret)
        array = ret.get('gradoEnt', [])
        return [("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep)) %
                    (it['gradoEnt']['codigoDescripcion']['codigo'], 
                     it['gradoEnt']['codigoDescripcion']['descripcion'],
                     it['gradoEnt']['valor'],
                     ) 
               for it in array]

    def ConsultarTipoCertificadoDeposito(self, sep="||"):
        "Consulta de tipos de Certificados de Depósito"
        ret = self.client.tipoCertificadoDepositoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoCertDepReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposCertDep', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoDeduccion(self, sep="||"):
        "Consulta de tipos de Deducciones"
        ret = self.client.tipoDeduccionConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoDeduccionReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposDeduccion', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoRetencion(self, sep="||"):
        "Consulta de tipos de Retenciones."
        ret = self.client.tipoRetencionConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoRetencionReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposRetencion', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarPuerto(self, sep="||"):
        "Consulta de Puertos habilitados"
        ret = self.client.puertoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['puertoReturn']
        self.__analizar_errores(ret)
        array = ret.get('puertos', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoActividad(self, sep="||"):
        "Consulta de Tipos de Actividad."
        ret = self.client.tipoActividadConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoActividadReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposActividad', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarProvincias(self, sep="||"):
        "Consulta las provincias habilitadas"
        ret = self.client.provinciasConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['provinciasReturn']
        self.__analizar_errores(ret)
        array = ret.get('provincias', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarLocalidadesPorProvincia(self, codigo_provincia, sep="||"):
        ret = self.client.localidadXProvinciaConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        codProvincia=codigo_provincia,
                        )['localidadesReturn']
        self.__analizar_errores(ret)
        array = ret.get('localidades', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTiposOperacion(self, sep="||"):
        "Consulta tipo de Operación por Actividad."
        ops = []
        ret = self.client.tipoActividadConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoActividadReturn']
        self.__analizar_errores(ret)
        for it_act in ret.get('tiposActividad', []):

            ret = self.client.tipoOperacionXActividadConsultar(
                            auth={
                                'token': self.Token, 'sign': self.Sign,
                                'cuit': self.Cuit, },
                            nroActLiquida=it_act['codigoDescripcion']['codigo'],
                            )['tipoOperacionReturn']
            self.__analizar_errores(ret)
            array = ret.get('tiposOperacion', [])
            ops.extend([("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep)) % 
                    (it_act['codigoDescripcion']['codigo'],
                     it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
                   for it in array])
        return ops

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = u"%s" % (e)
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = u"%s" % (e)

    def LoadTestXML(self, xml_file):
        "Cargar una respuesta predeterminada de pruebas (emulación del ws)"
        # cargo el ejemplo de AFIP (emulando respuesta del webservice)
        from pysimplesoap.transport import DummyTransport as DummyHTTP 
        xml = open(os.path.join(INSTALL_DIR, xml_file)).read()
        self.client.http = DummyHTTP(xml)

    def SetParametro(self, clave, valor):
        "Establece un parámetro general (usarse en llamadas posteriores)"
        # útil para parámetros de entrada (por ej. VFP9 no soporta más de 27)
        self.params[str(clave)] = valor
        return True

    def GetParametro(self, clave, clave1=None, clave2=None):
        "Devuelve un parámetro general (establecido por llamadas anteriores)"
        # útil para parámetros de salida (por ej. campos de TransaccionPlainWS)
        valor = self.params.get(clave)
        # busco datos "anidados" (listas / diccionarios)
        if clave1 is not None and valor is not None:
            if isinstance(clave1, basestring) and clave1.isdigit():
                clave1 = int(clave1)
            try:
                valor = valor[clave1]
            except (KeyError, IndexError):
                valor = None
        if clave2 is not None and valor is not None:
            try:
                valor = valor.get(clave2)
            except KeyError:
                valor = None
        if valor is not None:
            return str(valor)
        else:
            return ""

def escribir_archivo(dic, nombre_archivo, agrega=False):
    archivo = open(nombre_archivo, agrega and "a" or "w")
    dic['tipo_reg'] = 0
    archivo.write(escribir(dic, ENCABEZADO))
    if 'certificados' in dic:
        for it in dic['certificados']:
            it['tipo_reg'] = 1
            archivo.write(escribir(it, CERTIFICADO))
    if 'retenciones' in dic:
        for it in dic['retenciones']:
            it['tipo_reg'] = 2
            archivo.write(escribir(it, RETENCION))
    if 'deducciones' in dic:
        for it in dic['deducciones']:
            it['tipo_reg'] = 3
            archivo.write(escribir(it, DEDUCCION))
    if 'errores' in dic:
        for it in dic['errores']:
            it['tipo_reg'] = 'R'
            archivo.write(escribir(it, ERROR))
    archivo.close()

def leer_archivo(nombre_archivo):
    archivo = open(nombre_archivo, "r")
    dic = {'retenciones': [], 'deducciones': [], 'certificados': []}
    for linea in archivo:
        if str(linea[0])=='0':
            dic.update(leer(linea, ENCABEZADO))
        elif str(linea[0])=='1':
            dic['certificados'].append(leer(linea, CERTIFICADO))
        elif str(linea[0])=='2':
            dic['retenciones'].append(leer(linea, RETENCION))
        elif str(linea[0])=='3':
            dic['deducciones'].append(leer(linea, DEDUCCION))
        else:
            print "Tipo de registro incorrecto:", linea[0]
    archivo.close()
    return dic
    

# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)
    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in [('Encabezado', ENCABEZADO), 
                             ('Certificado', CERTIFICADO), 
                             ('Retencion', RETENCION), 
                             ('Deduccion', DEDUCCION), 
                             ('Evento', EVENTO), ('Error', ERROR)]:
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
        win32com.server.register.UseCommandLine(WSLPG)
        sys.exit(0)
        
    import csv
    from ConfigParser import SafeConfigParser

    import wsaa

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        if sys.argv[1:] and not sys.argv[1].startswith("--"):
            print "Usando configuración:", sys.argv[1]
            CONFIG_FILE = sys.argv[1]

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSLPG','CUIT')
        ENTRADA = config.get('WSLPG','ENTRADA')
        SALIDA = config.get('WSLPG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = wsaa.WSAAURL
        if config.has_option('WSLPG','URL') and not HOMO:
            WSLPG_url = config.get('WSLPG','URL')
        else:
            WSLPG_url = WSDL

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "WSLPG_url:", WSLPG_url
        # obteniendo el TA
        TA = "wslpg-ta.xml"
        if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
            tra = wsaa.create_tra(service="wslpg")
            if DEBUG:
                print tra
            cms = wsaa.sign_tra(tra, CERT, PRIVATEKEY)
            try:
                ta_string = wsaa.call_wsaa(cms, wsaa_url)
            except Exception, e:
                print e
                ta_string = ""
            open(TA,"w").write(ta_string)
        ta_string=open(TA).read()
        if ta_string:
            ta = SimpleXMLElement(ta_string)
            token = str(ta.credentials.token)
            sign = str(ta.credentials.sign)
        else:
            token = ""
            sign = ""
        # fin TA

        # cliente soap del web service
        wslpg = WSLPG()
        wslpg.LanzarExcepciones = True
        wslpg.Conectar(url=WSLPG_url)
        wslpg.Token = token
        wslpg.Sign = sign
        wslpg.Cuit = CUIT
        
        if '--dummy' in sys.argv:
            ret = wslpg.Dummy()
            print "AppServerStatus", wslpg.AppServerStatus
            print "DbServerStatus", wslpg.DbServerStatus
            print "AuthServerStatus", wslpg.AuthServerStatus
            ##sys.exit(0)

        if '--autorizar' in sys.argv or '--ajustar' in sys.argv:
        
            if '--prueba' in sys.argv:
                pto_emision = 99
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=pto_emision,
                    nro_orden=0,  # que lo calcule automáticamente
                    cuit_comprador=wslpg.Cuit, 
                    nro_act_comprador=36, nro_ing_bruto_comprador=wslpg.Cuit,
                    cod_tipo_operacion=1,
                    es_liquidacion_propia='N', es_canje='N',
                    cod_puerto=14, des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=31, 
                    cuit_vendedor=20267565393, nro_ing_bruto_vendedor=20267565393,
                    actua_corredor="N", liquida_corredor="N", cuit_corredor=20267565393,
                    comision_corredor=1, nro_ing_bruto_corredor=20267565393,
                    fecha_precio_operacion="2013-02-07",
                    precio_ref_tn=2000,
                    cod_grado_ref="G1",
                    cod_grado_ent="G1",
                    factor_ent=98,
                    precio_flete_tn=10,
                    cont_proteico=20,
                    alic_iva_operacion=10.5,
                    campania_ppal=1213,
                    cod_localidad_procedencia=3,
                    cod_prov_procedencia=1,
                    datos_adicionales="DATOS ADICIONALES",
                    ##peso_neto_sin_certificado=2000,
                    precio_operacion=1970,  # para probar ajustar
                    total_peso_neto=1000,   # para probar ajustar
                    certificados=[dict(   
                        tipo_certificado_deposito=5,
                        nro_certificado_deposito=555501200623,
                        peso_neto=1000,
                        cod_localidad_procedencia=3,
                        cod_prov_procedencia=1,
                        campania=1213,
                        fecha_cierre="2013-01-13",)],
                    retenciones=[dict(
                            codigo_concepto="RI",
                            detalle_aclaratorio="DETALLE DE IVA",
                            base_calculo=1970,
                            alicuota=10.5,
                        ), dict(
                            codigo_concepto="RG",
                            detalle_aclaratorio="DETALLE DE GANANCIAS",
                            base_calculo=100,
                            alicuota=15,
                        )],
                    deducciones=[dict(
                            codigo_concepto="OD",
                            detalle_aclaratorio="FLETE",
                            dias_almacenaje="0",
                            precio_pkg_diario=0.0,
                            comision_gastos_adm=0.0,
                            base_calculo=100.0,
                            alicuota=21.0,
                        )],
                    )
                escribir_archivo(dic, ENTRADA)
            else:
                dic = leer_archivo(ENTRADA)

            if dic['nro_orden'] == 0:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarUltNroOrden(pto_emision)
                if ok:
                    dic['nro_orden'] = wslpg.NroOrden + 1

            if dic['actua_corredor'] == "N":
                # borrando datos corredor si no corresponden
                ##dic['liquida_corredor'] = "N"
                dic['cuit_corredor'] = None
                dic['comision_corredor'] = None
                dic['nro_ing_bruto_corredor'] = None
            
            if not dic.get("peso_neto_sin_certificado") or dic['certificados']:
                # si no corresponde elimino este campo opcional
                if "peso_neto_sin_certificado" in dic:
                    del dic['peso_neto_sin_certificado']

            # establezco los parametros (se pueden pasar directamente al metodo)
            for k, v in sorted(dic.items()):
                if DEBUG: print "%s = %s" % (k, v)
                wslpg.SetParametro(k, v)
                
            # cargo la liquidación:
            wslpg.CrearLiquidacion()

            for cert in dic['certificados']:
                wslpg.AgregarCertificado(**cert)

            for ded in dic['deducciones']:
                wslpg.AgregarDeduccion(**ded)

            for ret in dic['retenciones']:
                wslpg.AgregarRetencion(**ret)

            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo
                if '--error' in sys.argv:
                    wslpg.LoadTestXML("wslpg_error.xml")     # cargo error
                else:
                    wslpg.LoadTestXML("wslpg_aut_test.xml")  # cargo respuesta

            print "Liquidacion: pto_emision=%s nro_orden=%s nro_act=%s tipo_op=%s" % (
                    wslpg.liquidacion['ptoEmision'], 
                    wslpg.liquidacion['nroOrden'], 
                    wslpg.liquidacion['nroActComprador'],
                    wslpg.liquidacion['codTipoOperacion'], 
                    )
        
            if '--ajustar' in sys.argv:
                print "Ajustando..."
                i = sys.argv.index("--ajustar")
                if i + 2 > len(sys.argv) or sys.argv[i + 1].startswith("--"):
                    coe_ajustado = raw_input("Ingrese COE ajustado: ")
                    cod_tipo_ajuste = raw_input("Ingrese Tipo Ajuste: ")
                else:
                    coe_ajustado = sys.argv[i + 1]
                    cod_tipo_ajuste = sys.argv[i + 2]
                ret = wslpg.AjustarLiquidacion(
                                coe_ajustado=coe_ajustado,
                                cod_tipo_ajuste=cod_tipo_ajuste,
                                precio_operacion=dic['precio_operacion'],
                                total_peso_neto=dic['total_peso_neto'])
            else:
                print "Autorizando..." 
                ret = wslpg.AutorizarLiquidacion()

            print "Errores:", wslpg.Errores
            print "COE", wslpg.COE
            print "COEAjustado", wslpg.COEAjustado
            print "TootalDeduccion", wslpg.TotalDeduccion
            print "TotalRetencion", wslpg.TotalRetencion
            print "TotalRetencionAfip", wslpg.TotalRetencionAfip
            print "TotalOtrasRetenciones", wslpg.TotalOtrasRetenciones
            print "TotalNetoAPagar", wslpg.TotalNetoAPagar
            print "TotalIvaRg2300_07", wslpg.TotalIvaRg2300_07
            print "TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion
            if '--testing' in sys.argv:
                assert wslpg.COE == "330100000357"
                assert wslpg.COEAjustado == None
                assert wslpg.Estado == "AC"
                assert wslpg.TotalPagoSegunCondicion == 1968.00
                assert wslpg.GetParametro("fecha_liquidacion") == "07/02/2013"
                assert wslpg.GetParametro("retenciones", 1, "importe_retencion") == "157.60"

            if DEBUG: 
                pprint.pprint(wslpg.params)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params)
            escribir_archivo(dic, SALIDA)
            sys.exit(0)            

        if '--anular' in sys.argv:
            ##print wslpg.client.help("anularLiquidacion")
            try:
                coe = sys.argv[sys.argv.index("--anular") + 1]
            except IndexError:
                coe = 330100000357

            print "Anulando COE", coe
            ret = wslpg.AnularLiquidacion(coe)
            print "COE", wslpg.COE
            print "Resultado", wslpg.Resultado
            print "Errores:", wslpg.Errores
            sys.exit(0)

        if '--consultar' in sys.argv:
            pto_emision = None
            nro_orden = 0
            coe = None
            try:
                pto_emision = sys.argv[sys.argv.index("--consultar") + 1]
                nro_orden = sys.argv[sys.argv.index("--consultar") + 2]
                coe = sys.argv[sys.argv.index("--consultar") + 3]
            except IndexError:
                pass
            print "Consultando: pto_emision=%s nro_orden=%s coe=%s" % (pto_emision, nro_orden, coe)
            ret = wslpg.ConsultarLiquidacion(pto_emision=pto_emision, nro_orden=nro_orden, coe=coe)
            print "COE", wslpg.COE
            print "Estado", wslpg.Estado
            print "Errores:", wslpg.Errores

            # actualizo el archivo de salida con los datos devueltos
            escribir_archivo(wslpg.params, SALIDA)

            if DEBUG: 
                pprint.pprint(wslpg.params)
            sys.exit(0)

        if '--ult' in sys.argv:
            try:
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError, ValueError:
                pto_emision = 1
            print "Consultando ultimo nro_orden para pto_emision=%s" % pto_emision
            ret = wslpg.ConsultarUltNroOrden()
            print "Ultimo Nro de Orden", wslpg.NroOrden
            print "Errores:", wslpg.Errores
            sys.exit(0)


        # Recuperar parámetros:
        
        if '--campanias' in sys.argv:
            ret = wslpg.ConsultarCampanias()
            print "\n".join(ret)
        
        if '--tipograno' in sys.argv:
            ret = wslpg.ConsultarTipoGrano()
            print "\n".join(ret)

        if '--gradoref' in sys.argv:
            ret = wslpg.ConsultarCodigoGradoReferencia()
            print "\n".join(ret)

        if '--gradoentregado' in sys.argv:
            ##wslpg.LoadTestXML("wslpg_cod.xml")     # cargo respuesta de ej
            cod_grano = raw_input("Ingrese el código de grano: ")
            ret = wslpg.ConsultarGradoEntregadoXTipoGrano(cod_grano=cod_grano)
            print "\n".join(ret)

        if '--certdeposito' in sys.argv:
            ret = wslpg.ConsultarTipoCertificadoDeposito()
            print "\n".join(ret)

        if '--deducciones' in sys.argv:
            ret = wslpg.ConsultarTipoDeduccion()
            print "\n".join(ret)

        if '--retenciones' in sys.argv:
            ret = wslpg.ConsultarTipoRetencion()
            print "\n".join(ret)
            
        if '--puertos' in sys.argv:
            ret = wslpg.ConsultarPuerto()
            print "\n".join(ret)

        if '--actividades' in sys.argv:
            ret = wslpg.ConsultarTipoActividad()
            print "\n".join(ret)

        if '--operaciones' in sys.argv:
            ret = wslpg.ConsultarTiposOperacion()
            print "\n".join(ret)

        if '--provincias' in sys.argv:
            ret = wslpg.ConsultarProvincias()
            print "\n".join(ret)
                    
        if '--localidades' in sys.argv:    
            ret = wslpg.ConsultarLocalidadesPorProvincia(11)
            print "\n".join(ret)
            
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
    finally:
        if XML:
            open("wslpg_request.xml", "w").write(wslpg.client.xml_request)
            open("wslpg_response.xml", "w").write(wslpg.client.xml_response)

