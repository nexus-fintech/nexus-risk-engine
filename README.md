# **Nexus Risk Engine 🧠**

[![CI](https://github.com/nexus-fintech/nexus-risk-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/nexus-fintech/nexus-risk-engine/actions/workflows/ci.yml)

**Microservicio de evaluación de riesgo crediticio potenciado por Inteligencia Artificial. Actúa como el "cerebro" analítico de la plataforma Nexus Finance.**

## **📖 Descripción**

Este servicio es **Stateless** (sin estado) y utiliza un enfoque **Híbrido** de alto rendimiento:

1.  **Machine Learning:** Un **Random Forest Classifier** estima la probabilidad de que una solicitud se apruebe a partir del ingreso, el monto, el plazo, la edad y la deuda mensual. Acierta el **97.8 %** de las decisiones en la parte del dataset que no vio al entrenar ([cómo se midió](#-desempeño-del-modelo)).
2.  **Lógica de Negocio:** Aplica reglas financieras pos-análisis para calcular límites de montos (capacidad de endeudamiento) y tasas de interés personalizadas basadas en el riesgo detectado.

Se comunica con el **Backend Core (Java)** mediante una API REST, desacoplando la lógica transaccional de la lógica analítica predictiva.

## **🏗️ Arquitectura del Proyecto**

Estructura optimizada para MLOps y Clean Architecture en Python:

```text
nexus-risk-engine/
├── app/
│   ├── api/          # Controladores REST (Endpoints expuestos)
│   ├── services/     # Servicio de Dominio (Carga del modelo .pkl y lógica)
│   ├── schemas/      # DTOs y Validación estricta (Pydantic)
│   └── core/         # Configuración y Variables de Entorno
├── nexus_credit_data.xlsx # Dataset de entrenamiento: 4,269 solicitudes con su decisión
├── nexus_risk_model.pkl   # Modelo serializado (El "Cerebro" de la IA)
├── train_risk_model.py    # Pipeline de entrenamiento (ETL + Training)
├── Dockerfile             # Definición de la imagen del contenedor (Incluye el modelo)
└── requirements.txt       # Dependencias de Python
```

## **🛠️ Stack Tecnológico**

| Componente        | Tecnología   | Versión  | Razón de Uso                                                         |
| :---------------- | :----------- | :------- | :------------------------------------------------------------------- |
| **Lenguaje**      | Python       | **3.12** | Última versión estable con optimizaciones significativas de memoria. |
| **Modelo IA**     | Scikit-learn | 1.7.2    | Versión fija: la misma con la que se entrenó el modelo `.pkl`.       |
| **API Framework** | FastAPI      | 0.115+   | Performance asíncrono y documentación automática (OpenAPI).          |
| **Serialización** | Joblib       | 1.4+     | Carga y guardado eficiente de modelos de ML pesados                  |
| **Procesamiento** | Pandas       | 2.2+     | Manipulación de vectores de datos y limpieza (ETL).                  |
| **Validación**    | Pydantic V2  | 2.5+     | Validación de datos de entrada ultra-rápida (Core en Rust).          |

## **⚙️ Capacidades del Motor**

### **Endpoint: POST /api/v1/evaluate-risk**

El motor recibe el perfil financiero, lo vectoriza y consulta al modelo .pkl.

Variables de Entrada (Features):

- **monthly_income:** Ingreso mensual declarado.
- **monthly_debt:** Deuda mensual actual.
- **requested_amount:** Monto solicitado.
- **term_in_months:** Plazo del préstamo.
- **age:** Edad del solicitante.

**Respuesta Inteligente:**

- score: Puntaje FICO simulado derivado de la probabilidad de aprobación (Escala 300-850).
- risk_level: Clasificación de riesgo (LOW, MEDIUM, HIGH).
- is_approved: Decisión booleana final.
- suggested_interest_rate: Tasa dinámica basada en el riesgo.
- max_approved_amount: Cálculo de capacidad de endeudamiento basado en ingresos y riesgo.

## **🧠 Entrenamiento del Modelo (ML Pipeline)**

El proyecto incluye un script de entrenamiento automatizado. Si se actualizan los datos en nexus_credit_data.xlsx, se debe re-entrenar el cerebro:

```bash
# Ejecutar pipeline de entrenamiento
python train_risk_model.py
```

Nota: Esto generará un nuevo archivo nexus_risk_model.pkl. Para que el cambio surta efecto en producción, se debe reconstruir el contenedor Docker.

## **📊 Desempeño del modelo**

El dataset (`nexus_credit_data.xlsx`) tiene 4,269 solicitudes, el 59 % aprobadas. El script de entrenamiento separa el 20 % al azar (`random_state=42`) y entrena con el resto. Sobre ese 20 % (854 solicitudes que el modelo no vio), el modelo publicado `nexus_risk_model.pkl` obtiene:

| Métrica | Valor |
| :--- | :--- |
| Exactitud | **97.8 %** (la clase mayoritaria sola daría 58.7 %) |
| ROC-AUC | 0.998 |
| Aprobaciones que el modelo rechazaría | 6 de 501 |
| Rechazos que el modelo aprobaría | 13 de 353 |

La deuda mensual es la variable que más pesa (59 % de la importancia), seguida del ingreso (23 %) y el monto (12 %).

Estas cifras miden qué tan bien el modelo reproduce las decisiones de este dataset. No está validado con la cartera de una entidad financiera, así que no son una predicción de impago real.

## **🧪 Pruebas**

46 pruebas automatizadas con **pytest** (97 % de cobertura sobre `app/`) que corren en cada push con GitHub Actions:

| Archivo | Qué verifica |
| :--- | :--- |
| `tests/test_risk_evaluator.py` | Reglas de negocio con un modelo simulado: escala 300-850, umbrales de riesgo, umbral de aprobación, monto máximo y tasa por nivel de riesgo |
| `tests/test_schemas.py` | Validación de la solicitud: rangos de edad, plazo y montos |
| `tests/test_api.py` | Contrato de la API: 200, 422, 503 sin modelo y 500 sin exponer detalles internos |
| `tests/test_model.py` | El modelo entrenado: variables esperadas, probabilidades válidas y orden lógico entre perfiles |

```bash
pip install -r requirements.txt pytest-cov
pytest --cov=app
```

## **🚀 Ejecución y Despliegue**

### **Docker (Producción)**

La imagen Docker está configurada para autocontener el modelo, copiando el cerebro (.pkl) y los recursos necesarios al momento de la construcción.

```bash
# 1. Construir la imagen (necesario si cambió el modelo .pkl)
docker-compose build

# 2. Levantar el servicio
docker-compose up -d
```

### **Documentación Automática**

FastAPI genera documentación interactiva automáticamente para probar el modelo sin necesidad de Frontend:

- 👉 **Swagger/OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 👉 **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## **👤 Autor**

**Angel Antonio Cancho Corilla** \- Software Engineer & AI Integration
