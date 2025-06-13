import pandas as pd
from sqlalchemy import create_engine
from model import db, cie10
from app import app
import os

def cargar_cie10():
    with app.app_context():
        try:
            # Leer el archivo CSV
            print("Leyendo archivo CIE-10.csv...")
            df = pd.read_csv('CIE-10.csv', encoding='utf-8', 
                           names=['codigo_corto', 'descripcion_corta', 'codigo', 'descripcion'],
                           skiprows=1)  # Saltar la fila de encabezados
            
            # Crear la tabla si no existe
            db.create_all()
            
            # Limpiar la tabla existente
            print("Limpiando tabla existente...")
            cie10.query.delete()
            db.session.commit()
            
            # Preparar los datos para inserción
            print("Preparando datos para inserción...")
            total_registros = len(df)
            print(f"Total de registros a procesar: {total_registros}")
            
            # Insertar los datos en lotes
            print("Insertando datos en la base de datos...")
            batch_size = 1000
            registros_exitosos = 0
            registros_fallidos = 0
            
            for i in range(0, total_registros, batch_size):
                batch_df = df.iloc[i:i + batch_size]
                for _, row in batch_df.iterrows():
                    try:
                        registro = cie10(
                            codigo=str(row['codigo']).strip(),
                            descripcion=str(row['descripcion']).strip(),
                            categoria=str(row['codigo_corto']).strip(),
                            subcategoria=str(row['descripcion_corta']).strip()
                        )
                        db.session.add(registro)
                        registros_exitosos += 1
                    except Exception as e:
                        print(f"Error al procesar registro: {row}")
                        print(f"Error específico: {str(e)}")
                        registros_fallidos += 1
                        continue
                
                try:
                    db.session.commit()
                    print(f"Procesados {min(i + batch_size, total_registros)} de {total_registros} registros...")
                    print(f"Registros exitosos: {registros_exitosos}, Fallidos: {registros_fallidos}")
                except Exception as e:
                    print(f"Error al guardar lote: {str(e)}")
                    db.session.rollback()
            
            print("¡Carga completada exitosamente!")
            print(f"Resumen final - Registros exitosos: {registros_exitosos}, Fallidos: {registros_fallidos}")
            
        except Exception as e:
            print(f"Error durante la carga: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    cargar_cie10() 