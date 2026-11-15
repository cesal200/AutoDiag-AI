"""Taxonomía de síntomas y causas para el pre-diagnóstico mecánico."""

TAXONOMIA = {
    'motor': {
        'etiqueta': 'Motor y combustión',
        'palabras': [
            'motor', 'vibracion', 'vibración', 'tironea', 'tironeo', 'ahogo',
            'golpeteo', 'ruido motor', 'humo', 'aceite', 'sobrecalentamiento',
            'temperatura', 'inyeccion', 'inyección', 'bujia', 'bujía', 'bobina',
            'catalizador', 'escape negro', 'falla motor', 'check engine',
        ],
        'riesgo': 'PRECAUCION',
        'causas': [
            ('Falla de encendido en bujías o bobinas', 34),
            ('Mezcla pobre o inyección obstruida', 27),
            ('Sensor de oxígeno o catalizador degradado', 18),
        ],
        'pruebas': [
            ('Lectura de códigos OBD-II', 'Conectar escáner y registrar códigos activos y pendientes.', 'Sin códigos de falla o códigos coherentes con el síntoma.'),
            ('Prueba de compresión en cilindros', 'Medir compresión en cada cilindro con motor a temperatura de operación.', 'Diferencia menor al 10% entre cilindros y dentro del rango del fabricante.'),
            ('Inspección de bujías y bobinas', 'Retirar bujías, revisar electrodos y probar continuidad de bobinas.', 'Bujías sin desgaste excesivo y chispa constante.'),
        ],
    },
    'frenos': {
        'etiqueta': 'Sistema de frenos',
        'palabras': [
            'freno', 'frenos', 'chirrido', 'chillido', 'pedal', 'pastilla',
            'disco', 'abs', 'vibracion al frenar', 'vibración al frenar',
            'fuga de liquido de frenos', 'fuga de líquido de frenos',
        ],
        'riesgo': 'NO_MOVER_GRUA',
        'causas': [
            ('Pastillas o discos de freno desgastados', 38),
            ('Aire o fuga en el circuito hidráulico', 24),
            ('Sensor ABS o rodamiento con juego', 17),
        ],
        'pruebas': [
            ('Medición de espesor de pastillas y discos', 'Medir con calibrador en cada rueda.', 'Espesor por encima del mínimo del fabricante.'),
            ('Purga y prueba de estanqueidad', 'Revisar fugas y purgar el circuito hidráulico.', 'Pedal firme, sin fugas ni pérdida de presión.'),
            ('Lectura de códigos ABS', 'Escanear el módulo ABS y revisar sensores.', 'Sin códigos activos y lecturas de rueda estables.'),
        ],
    },
    'transmision': {
        'etiqueta': 'Transmisión y embrague',
        'palabras': [
            'transmision', 'transmisión', 'caja', 'embrague', 'clutch', 'patina',
            'patina el clutch', 'cambio', 'cambios', 'engranaje', 'diferencial',
            'ruido al cambiar', 'no entra la marcha',
        ],
        'riesgo': 'PRECAUCION',
        'causas': [
            ('Embrague desgastado o mal ajustado', 35),
            ('Nivel o calidad del aceite de transmisión inadecuada', 25),
            ('Sincronizadores o rodamientos internos desgastados', 20),
        ],
        'pruebas': [
            ('Prueba de patinaje del embrague', 'Aplicar carga en marcha alta y observar régimen del motor.', 'El régimen no sube sin aumento proporcional de velocidad.'),
            ('Inspección y nivel de aceite de caja', 'Revisar nivel, color y presencia de partículas metálicas.', 'Aceite limpio, nivel correcto y sin partículas.'),
            ('Prueba de cambios en ruta', 'Realizar cambios secuenciales con carga moderada.', 'Cambios suaves, sin ruidos ni bloqueos.'),
        ],
    },
    'suspension': {
        'etiqueta': 'Suspensión y dirección',
        'palabras': [
            'suspension', 'suspensión', 'amortiguador', 'resorte', 'direccion',
            'dirección', 'volante', 'rin', 'llanta', 'vibracion', 'vibración',
            'ruido al pasar', 'bache', 'desalineado', 'se va a un lado',
        ],
        'riesgo': 'PRECAUCION',
        'causas': [
            ('Amortiguadores o bujes desgastados', 33),
            ('Desalineación o desbalanceo de ruedas', 28),
            ('Rótulas o terminales de dirección con juego', 21),
        ],
        'pruebas': [
            ('Prueba de rebote y revisión visual', 'Empujar cada esquina y revisar fugas en amortiguadores.', 'Retorno controlado y sin fugas.'),
            ('Alineación y balanceo', 'Medir alineación y balancear las cuatro ruedas.', 'Valores dentro de especificación y sin vibración.'),
            ('Revisión de juego en rótulas', 'Elevar el vehículo y comprobar holguras con palanca.', 'Sin juego excesivo ni ruidos.'),
        ],
    },
    'electrico': {
        'etiqueta': 'Sistema eléctrico y electrónico',
        'palabras': [
            'electrico', 'eléctrico', 'bateria', 'batería', 'alternador', 'fusible',
            'luces', 'tablero', 'testigo', 'sensor', 'corto', 'no enciende',
            'descarga', 'arranque', 'marcha',
        ],
        'riesgo': 'PRECAUCION',
        'causas': [
            ('Batería descargada o alternador con baja carga', 36),
            ('Conexión o fusible con resistencia alta', 26),
            ('Sensor o módulo electrónico con falla intermitente', 19),
        ],
        'pruebas': [
            ('Prueba de batería y carga', 'Medir voltaje en reposo, con carga y durante arranque.', '12.4-12.8 V en reposo y 13.8-14.6 V con motor encendido.'),
            ('Inspección de fusibles y conectores', 'Revisar continuidad y limpieza de terminales.', 'Continuidad correcta y sin corrosión.'),
            ('Escaneo de módulos electrónicos', 'Leer códigos y datos en vivo de los módulos afectados.', 'Sin códigos activos ni valores fuera de rango.'),
        ],
    },
    'refrigeracion': {
        'etiqueta': 'Refrigeración',
        'palabras': [
            'refrigerante', 'radiador', 'agua', 'sobrecalentamiento', 'temperatura',
            'ventilador', 'termostato', 'manguera', 'fuga', 'vapor',
        ],
        'riesgo': 'NO_MOVER_GRUA',
        'causas': [
            ('Bajo nivel o fuga en el circuito de refrigeración', 37),
            ('Termostato o ventilador con funcionamiento deficiente', 25),
            ('Bomba de agua o radiador obstruido', 18),
        ],
        'pruebas': [
            ('Prueba de presión del sistema', 'Presurizar el circuito y buscar fugas.', 'Sin caída de presión ni fugas visibles.'),
            ('Prueba de ventilador y termostato', 'Verificar activación por temperatura y apertura del termostato.', 'Ventilador y termostato operan dentro del rango.'),
            ('Inspección de bomba y radiador', 'Revisar caudal, obstrucciones y estado de aletas.', 'Caudal correcto y radiador sin obstrucción.'),
        ],
    },
}

CAUSAS_GENERALES = [
    ('Falta de mantenimiento preventivo', 30),
    ('Desgaste natural de componentes', 24),
    ('Conexión eléctrica o sensor con falla intermitente', 18),
]

PALABRAS_RIESGO_ALTO = [
    'freno', 'frenos', 'fuga de combustible', 'fuga de gasolina', 'humo intenso',
    'sobrecalentamiento', 'temperatura alta', 'direccion', 'dirección',
    'no gira', 'bloqueado', 'incendio', 'olor a quemado',
]

PALABRAS_RIESGO_BAJO = [
    'ruido leve', 'testigo', 'luces', 'radio', 'aire acondicionado',
    'pequeño', 'leve', 'intermitente',
]


def normalizar_texto(texto):
    import unicodedata

    texto = (texto or '').lower()
    return ''.join(
        caracter for caracter in unicodedata.normalize('NFD', texto)
        if unicodedata.category(caracter) != 'Mn'
    )


def componentes_detectados(texto):
    texto = normalizar_texto(texto)
    detectados = []
    for clave, datos in TAXONOMIA.items():
        coincidencias = [
            palabra for palabra in datos['palabras']
            if normalizar_texto(palabra) in texto
        ]
        if coincidencias:
            detectados.append((clave, datos, coincidencias))
    return detectados
