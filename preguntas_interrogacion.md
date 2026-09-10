# Preguntas posibles para la interrogacion

## 1. Por que se utiliza un archivo JSON?

Para trabajar con datos ficticios sin depender de una carga inicial en la base de datos. `data_loader.py` abre el archivo y lo convierte en diccionarios y listas de Python.

## 2. Que hace un serializer?

Valida y transforma datos Python para que DRF pueda devolverlos como JSON. En este proyecto se utiliza `serializers.Serializer` porque los datos vienen del JSON y no de consultas a modelos.

## 3. Que hace `@api_view(['GET'])`?

Indica que la funcion es un endpoint de Django REST Framework y que acepta peticiones GET.

## 4. Como se muestra el nombre del profesor?

El curso contiene `teacher_id`. La funcion `courses_with_teacher_name()` crea un diccionario de docentes y busca el nombre correspondiente a cada curso.

## 5. Que hace `fetch()`?

Realiza una peticion HTTP asincrona desde el navegador. Luego `response.json()` convierte la respuesta en datos JavaScript para construir las filas de la tabla.

## 6. Por que la ruta `/` no produce 404?

Porque `academic_project/urls.py` conecta la ruta vacia con `views.home`, que renderiza una plantilla HTML.

## 7. Que representa `StudentCourse`?

Es la tabla intermedia entre estudiantes y cursos. Contiene `student_id` y `course_id`, que forman la clave primaria compuesta del diagrama ER.
