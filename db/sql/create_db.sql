-- =============================================
-- EGI - Base de datos de Inventario ITU
-- =============================================

CREATE DATABASE ubicacion_db;
GO

USE ubicacion_db;
GO

CREATE TABLE aulas (
    id_aula   INT IDENTITY(1,1) PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL,
    tipo      VARCHAR(20)  NOT NULL CHECK (tipo IN ('aula','laboratorio')),
    piso      INT,
    edificio  VARCHAR(50)
);
GO

CREATE TABLE responsables (
    id_responsable INT IDENTITY(1,1) PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    apellido       VARCHAR(100) NOT NULL,
    email          VARCHAR(150) UNIQUE NOT NULL
);
GO

CREATE TABLE equipos (
    id_equipo         VARCHAR(20)  PRIMARY KEY,
    codigo_inventario VARCHAR(50)  UNIQUE NOT NULL,
    id_aula           INT          NOT NULL,
    numero_banco      VARCHAR(10)  NOT NULL,
    estado            VARCHAR(20)  NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo','en_reparacion','baja','disponible','asignado')),
    id_responsable    INT,
    fecha_ingreso     DATE         NOT NULL,
    FOREIGN KEY (id_aula)        REFERENCES aulas(id_aula),
    FOREIGN KEY (id_responsable) REFERENCES responsables(id_responsable)
);
GO

CREATE TABLE asignaciones (
    id_asignacion INT IDENTITY(1,1) PRIMARY KEY,
    id_equipo     VARCHAR(20) NOT NULL,
    usuario_uid   VARCHAR(50) NOT NULL,
    rol_asignado  VARCHAR(20) NOT NULL CHECK (rol_asignado IN ('alumno','docente','tecnico')),
    fecha_desde   DATE        NOT NULL,
    fecha_hasta   DATE,
    activa        BIT         NOT NULL DEFAULT 1,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo)
);
GO

CREATE TABLE mantenimientos (
    id_mant      INT IDENTITY(1,1) PRIMARY KEY,
    id_equipo    VARCHAR(20)  NOT NULL,
    fecha_mant   DATE         NOT NULL,
    tipo         VARCHAR(30)  NOT NULL CHECK (tipo IN ('preventivo','correctivo','limpieza')),
    descripcion  VARCHAR(500),
    tecnico      VARCHAR(100),
    proximo_mant DATE,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo)
);
GO

-- DATOS DE PRUEBA
INSERT INTO aulas (nombre, tipo, piso, edificio) VALUES
('Laboratorio 1', 'laboratorio', 1, 'Edificio A'),
('Laboratorio 2', 'laboratorio', 1, 'Edificio A'),
('Laboratorio 3', 'laboratorio', 2, 'Edificio B');
GO

INSERT INTO responsables (nombre, apellido, email) VALUES
('Carlos',  'Mendez',  'cmendez@itu.edu.ar'),
('Laura',   'Gomez',   'lgomez@itu.edu.ar'),
('Roberto', 'Sanchez', 'rsanchez@itu.edu.ar');
GO

INSERT INTO equipos (id_equipo, codigo_inventario, id_aula, numero_banco, estado, id_responsable, fecha_ingreso) VALUES
('PC-LAB1-001', 'INV-2023-001', 1, 'B01', 'activo',        1, '2023-03-01'),
('PC-LAB1-002', 'INV-2023-002', 1, 'B02', 'activo',        1, '2023-03-01'),
('PC-LAB1-003', 'INV-2023-003', 1, 'B03', 'activo',        1, '2023-03-01'),
('PC-LAB2-001', 'INV-2023-004', 2, 'B01', 'asignado',      2, '2023-03-15'),
('PC-LAB2-002', 'INV-2023-005', 2, 'B02', 'activo',        2, '2023-03-15'),
('PC-LAB2-003', 'INV-2023-006', 2, 'B03', 'en_reparacion', 2, '2023-03-15'),
('PC-LAB3-001', 'INV-2023-007', 3, 'B01', 'activo',        3, '2023-04-01'),
('PC-LAB3-002', 'INV-2023-008', 3, 'B02', 'activo',        3, '2023-04-01'),
('NB-LAB1-001', 'INV-2024-001', 1, 'B10', 'asignado',      1, '2024-01-10'),
('NB-LAB1-002', 'INV-2024-002', 1, 'B11', 'activo',        1, '2024-01-10');
GO

INSERT INTO asignaciones (id_equipo, usuario_uid, rol_asignado, fecha_desde, fecha_hasta, activa) VALUES
('PC-LAB2-001', 'tecnico.inventario', 'tecnico', '2025-03-01', NULL, 1),
('NB-LAB1-001', 'docente.inventario', 'docente', '2025-03-01', NULL, 1);
GO

INSERT INTO mantenimientos (id_equipo, fecha_mant, tipo, descripcion, tecnico, proximo_mant) VALUES
('PC-LAB1-001', '2025-01-15', 'preventivo', 'Limpieza general y actualizacion SO', 'Carlos Mendez',   '2025-07-15'),
('PC-LAB1-002', '2025-01-15', 'preventivo', 'Limpieza general y actualizacion SO', 'Carlos Mendez',   '2025-07-15'),
('PC-LAB2-003', '2025-03-10', 'correctivo', 'Reemplazo de fuente de alimentacion', 'Roberto Sanchez', '2025-09-10'),
('PC-LAB3-001', '2025-02-20', 'limpieza',   'Limpieza de polvo interna',           'Laura Gomez',     '2025-08-20');
GO

-- PERMISOS POR GRUPOS DEL AD
USE master;
GO
CREATE LOGIN [ITU\G_Administradores] FROM WINDOWS;
CREATE LOGIN [ITU\G_Tecnicos]        FROM WINDOWS;
CREATE LOGIN [ITU\G_Docentes]        FROM WINDOWS;
CREATE LOGIN [ITU\G_Alumnos]         FROM WINDOWS;
GO

USE ubicacion_db;
GO
CREATE USER [ITU\G_Administradores] FOR LOGIN [ITU\G_Administradores];
ALTER ROLE db_owner      ADD MEMBER [ITU\G_Administradores];
GO
CREATE USER [ITU\G_Tecnicos] FOR LOGIN [ITU\G_Tecnicos];
ALTER ROLE db_datareader ADD MEMBER [ITU\G_Tecnicos];
ALTER ROLE db_datawriter ADD MEMBER [ITU\G_Tecnicos];
GO
CREATE USER [ITU\G_Docentes] FOR LOGIN [ITU\G_Docentes];
ALTER ROLE db_datareader ADD MEMBER [ITU\G_Docentes];
GO
CREATE USER [ITU\G_Alumnos] FOR LOGIN [ITU\G_Alumnos];
ALTER ROLE db_datareader ADD MEMBER [ITU\G_Alumnos];
GO