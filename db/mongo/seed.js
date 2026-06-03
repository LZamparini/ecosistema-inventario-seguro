// EGI - Ecosistema de Inventario Seguro
// Seed de la colecciÃ³n hardware en MongoDB

db = db.getSiblingDB('inventario');

db.hardware.drop();

db.hardware.insertMany([
  {
    id_equipo: "PC-LAB1-001",
    fabricante: "Dell",
    modelo: "OptiPlex 3080",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i5-10500", nucleos: 6, frecuencia_ghz: 3.1 },
    ram: { cantidad_gb: 16, tipo: "DDR4", frecuencia_mhz: 2666 },
    discos: [
      { tipo: "SSD", interfaz: "SATA", capacidad_gb: 480, marca: "Kingston" }
    ],
    sistema_operativo: { nombre: "Windows 11 Pro", version: "22H2" },
    perifericos: { monitor: "Dell 24\" E2422H", teclado: "Dell KB216", mouse: "Dell MS116" },
    fecha_registro: new Date("2023-03-01")
  },
  {
    id_equipo: "PC-LAB1-002",
    fabricante: "HP",
    modelo: "EliteDesk 800 G6",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i7-10700", nucleos: 8, frecuencia_ghz: 2.9 },
    ram: { cantidad_gb: 32, tipo: "DDR4", frecuencia_mhz: 2933 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 512, marca: "Samsung" },
      { tipo: "HDD", interfaz: "SATA", capacidad_gb: 1000, marca: "Seagate" }
    ],
    sistema_operativo: { nombre: "Windows 11 Pro", version: "22H2" },
    perifericos: { monitor: "HP 24mh 24\"", teclado: "HP 125", mouse: "HP 125" },
    fecha_registro: new Date("2023-03-01")
  },
  {
    id_equipo: "PC-LAB1-003",
    fabricante: "Lenovo",
    modelo: "ThinkCentre M720",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i5-8400", nucleos: 6, frecuencia_ghz: 2.8 },
    ram: { cantidad_gb: 8, tipo: "DDR4", frecuencia_mhz: 2400 },
    discos: [
      { tipo: "HDD", interfaz: "SATA", capacidad_gb: 500, marca: "WD" }
    ],
    sistema_operativo: { nombre: "Windows 10 Pro", version: "21H2" },
    perifericos: { monitor: "Lenovo 21.5\" T2224d", teclado: "Lenovo USB", mouse: "Lenovo USB" },
    fecha_registro: new Date("2023-03-01")
  },
  {
    id_equipo: "PC-LAB2-001",
    fabricante: "Dell",
    modelo: "OptiPlex 5090",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i5-10505", nucleos: 6, frecuencia_ghz: 3.2 },
    ram: { cantidad_gb: 16, tipo: "DDR4", frecuencia_mhz: 2666 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 256, marca: "Micron" }
    ],
    sistema_operativo: { nombre: "Ubuntu", version: "22.04 LTS" },
    perifericos: { monitor: "Dell 22\" SE2222H", teclado: "Dell KB216", mouse: "Dell MS116" },
    fecha_registro: new Date("2023-03-15")
  },
  {
    id_equipo: "PC-LAB2-002",
    fabricante: "HP",
    modelo: "ProDesk 400 G7",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i3-10100", nucleos: 4, frecuencia_ghz: 3.6 },
    ram: { cantidad_gb: 8, tipo: "DDR4", frecuencia_mhz: 2666 },
    discos: [
      { tipo: "SSD", interfaz: "SATA", capacidad_gb: 256, marca: "HP" }
    ],
    sistema_operativo: { nombre: "Windows 11 Pro", version: "22H2" },
    perifericos: { monitor: "HP V22 21.5\"", teclado: "HP 125", mouse: "HP 125" },
    fecha_registro: new Date("2023-03-15")
  },
  {
    id_equipo: "PC-LAB2-003",
    fabricante: "Lenovo",
    modelo: "ThinkCentre M90n",
    tipo: "desktop",
    cpu: { marca: "Intel", modelo: "Core i5-8265U", nucleos: 4, frecuencia_ghz: 1.6 },
    ram: { cantidad_gb: 8, tipo: "DDR4", frecuencia_mhz: 2400 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 128, marca: "Lenovo" }
    ],
    sistema_operativo: { nombre: "Windows 10 Pro", version: "21H2" },
    perifericos: { monitor: "Lenovo D22-20", teclado: "Lenovo USB", mouse: "Lenovo USB" },
    fecha_registro: new Date("2023-03-15")
  },
  {
    id_equipo: "PC-LAB3-001",
    fabricante: "Dell",
    modelo: "Precision 3650",
    tipo: "workstation",
    cpu: { marca: "Intel", modelo: "Xeon W-1350", nucleos: 6, frecuencia_ghz: 3.3 },
    ram: { cantidad_gb: 64, tipo: "ECC DDR4", frecuencia_mhz: 3200 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 512, marca: "Samsung" },
      { tipo: "HDD", interfaz: "SATA", capacidad_gb: 2000, marca: "Seagate" }
    ],
    gpu: { marca: "NVIDIA", modelo: "Quadro P2200", vram_gb: 5 },
    sistema_operativo: { nombre: "Windows 11 Pro", version: "22H2" },
    perifericos: { monitor: "Dell 27\" U2722D", teclado: "Dell KB216", mouse: "Dell MS3320W" },
    fecha_registro: new Date("2023-04-01")
  },
  {
    id_equipo: "PC-LAB3-002",
    fabricante: "HP",
    modelo: "Z2 G8 Tower",
    tipo: "workstation",
    cpu: { marca: "Intel", modelo: "Core i9-11900K", nucleos: 8, frecuencia_ghz: 3.5 },
    ram: { cantidad_gb: 32, tipo: "DDR4", frecuencia_mhz: 3200 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 1000, marca: "Samsung 980 Pro" }
    ],
    gpu: { marca: "AMD", modelo: "Radeon Pro W6400", vram_gb: 4 },
    sistema_operativo: { nombre: "Ubuntu", version: "22.04 LTS" },
    perifericos: { monitor: "HP Z27k G3 27\"", teclado: "HP USB", mouse: "HP USB" },
    fecha_registro: new Date("2023-04-01")
  },
  {
    id_equipo: "NB-LAB1-001",
    fabricante: "Lenovo",
    modelo: "ThinkPad E15 Gen 2",
    tipo: "laptop",
    cpu: { marca: "AMD", modelo: "Ryzen 5 4500U", nucleos: 6, frecuencia_ghz: 2.3 },
    ram: { cantidad_gb: 16, tipo: "DDR4", frecuencia_mhz: 3200 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 512, marca: "Kingston" }
    ],
    bateria: { capacidad_mah: 45000, autonomia_hs: 8 },
    pantalla: { tamano_pulgadas: 15.6, resolucion: "1920x1080" },
    sistema_operativo: { nombre: "Windows 11 Pro", version: "23H2" },
    perifericos: { teclado: "integrado", mouse: "Logitech M185" },
    fecha_registro: new Date("2024-01-10")
  },
  {
    id_equipo: "NB-LAB1-002",
    fabricante: "HP",
    modelo: "ProBook 450 G9",
    tipo: "laptop",
    cpu: { marca: "Intel", modelo: "Core i5-1235U", nucleos: 10, frecuencia_ghz: 1.3 },
    ram: { cantidad_gb: 8, tipo: "DDR4", frecuencia_mhz: 3200 },
    discos: [
      { tipo: "SSD", interfaz: "NVMe", capacidad_gb: 256, marca: "Micron" }
    ],
    bateria: { capacidad_mah: 41000, autonomia_hs: 7 },
    pantalla: { tamano_pulgadas: 15.6, resolucion: "1920x1080" },
    sistema_operativo: { nombre: "Windows 11 Pro", version: "22H2" },
    perifericos: { teclado: "integrado", mouse: "HP USB" },
    fecha_registro: new Date("2024-01-10")
  }
]);

print("Seed completado: " + db.hardware.countDocuments() + " documentos insertados.");