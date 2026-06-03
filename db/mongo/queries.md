\# Queries MongoDB — Defensa EGI



\## Cómo entrar al shell de MongoDB

kubectl exec -it deploy/inventario-db -n inventario-seguro -- mongo -u root -p MongoPass123



\## Una vez adentro, seleccionar la base

use inventario



\## 1. Ver todos los documentos

db.hardware.find().pretty()



\## 2. Buscar solo laptops

db.hardware.find({ tipo: "laptop" }).pretty()



\## 3. Equipos con 16 GB de RAM o más

db.hardware.find({ "ram.cantidad\_gb": { $gte: 16 } })



\## 4. Equipos con GPU (workstations)

db.hardware.find({ gpu: { $exists: true } })



\## 5. Contar equipos por tipo

db.hardware.aggregate(\[{ $group: { \_id: "$tipo", total: { $sum: 1 } } }])



\## 6. Actualizar RAM de un equipo

db.hardware.updateOne(

&#x20; { id\_equipo: "PC-LAB1-003" },

&#x20; { $set: { "ram.cantidad\_gb": 16 } }

)



\## 7. Agregar un disco a un equipo

db.hardware.updateOne(

&#x20; { id\_equipo: "PC-LAB1-003" },

&#x20; { $push: { discos: { tipo: "SSD", interfaz: "SATA", capacidad\_gb: 240, marca: "Kingston" } } }

)



\## 8. Eliminar un documento

db.hardware.deleteOne({ id\_equipo: "NB-LAB1-002" })



\## 9. Verificar cuántos quedan

db.hardware.countDocuments()

