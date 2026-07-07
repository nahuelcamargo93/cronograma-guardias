-- QUERIES DE ACTUALIZACION DE PERSONAL --
UPDATE personal SET categoria = 'A', rol = 'Supervisor suplente', activo = 1 WHERE nombre = 'FERNANDEZ Juan Emir';
UPDATE personal SET categoria = 'A', rol = 'Monitorista', activo = 1 WHERE nombre = 'SUÑER Mara Tatiana';
UPDATE personal SET categoria = 'B', rol = 'Monitorista', activo = 1 WHERE nombre = 'OJEDA Miriam';
UPDATE personal SET categoria = 'B', rol = 'Monitorista', activo = 1 WHERE nombre = 'FERNANDEZ Claudia Elizabeth';
UPDATE personal SET categoria = 'D', rol = 'Monitorista', activo = 1 WHERE nombre = 'VILLEGAS Gaston';
UPDATE personal SET categoria = 'D', rol = 'Supervisor Suplente', activo = 1 WHERE nombre = 'QUINTANA Felipe Gabriel';

-- QUERIES DE ACTUALIZACION DE PUESTOS --
DELETE FROM personal_puestos WHERE personal_nombre = 'FERNANDEZ Juan Emir';
INSERT INTO personal_puestos (personal_nombre, puesto_id, es_primario, servicio_id) VALUES ('FERNANDEZ Juan Emir', 31, 1, 4);
DELETE FROM personal_puestos WHERE personal_nombre = 'OJEDA Miriam';
INSERT INTO personal_puestos (personal_nombre, puesto_id, es_primario, servicio_id) VALUES ('OJEDA Miriam', 32, 1, 4);
DELETE FROM personal_puestos WHERE personal_nombre = 'RUOCCO MUÑOZ Luis Alfredo';
INSERT INTO personal_puestos (personal_nombre, puesto_id, es_primario, servicio_id) VALUES ('RUOCCO MUÑOZ Luis Alfredo', 31, 1, 4);
DELETE FROM personal_puestos WHERE personal_nombre = 'FERNANDEZ Claudia Elizabeth';
INSERT INTO personal_puestos (personal_nombre, puesto_id, es_primario, servicio_id) VALUES ('FERNANDEZ Claudia Elizabeth', 32, 1, 4);

-- QUERIES DE ACTUALIZACION DE EXCLUSIONES DE TURNOS --
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('FERNANDEZ Celeste Ivana', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('FERNANDEZ Juan Emir', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('GIMENEZ Adriana', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('OLGUIN ALDECO Jennifer Sofia', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('ESCUDERO Gabriela', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('VILLEGAS Angel', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('ROMERO Tomas', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('SUÑER Mara Tatiana', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "06-12_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('ALCARAZ Xavier', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('OJEDA Miriam', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('RUOCCO MUÑOZ Luis Alfredo', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('STEIMBRECHER Yolanda', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('LEDESMA PAZ Micaela', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('MANSILLA Diego', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('MESSINA Eduardo', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('RODRIGUEZ Maximiliano', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('SANCIO Paola', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('FLORES Jose Nicolas', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('FERNANDEZ Claudia Elizabeth', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "12-18_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "12-18_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('BARROSO Alan', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('BRIZUELA Irma', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('GUERRERO Cesar', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('MOCDESE Marcelo Leonel', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('TORRES Yesica', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('VERGARA Nazareno', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('CANO Avril', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "18-24_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "18-24_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('FUNEZ Valeria Vanesa', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('VILLEGAS Gaston', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('QUINTANA Felipe Gabriel', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('MIRANDA Luis', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('MUÑOZ Maria Carolina', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('SUAREZ Carolina', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('VELEZ Facundo', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('VERGARA Mariano', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '[
  {
    "turnos": [
      "00-06_Supervisor",
      "06-12_Supervisor",
      "12-18_Supervisor",
      "00-06_Monitorista",
      "06-12_Monitorista",
      "12-18_Monitorista",
      "Administrativo"
    ],
    "dias": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ]
  }
]', 1, 4);
