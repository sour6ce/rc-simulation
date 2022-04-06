# rc-simulation
*Gabriel Hernández Rodríguez C311*

*Dennis Fiallo Muñoz C311*

## Ejecución

Para ejecutar la simulación basta con correr `simul.py` en el terminal. Se adjunta un archivo con las librerías requeridas de Python para ejecutar la app.

Al ejecutar el script sin pasarle parámetros buscará un archivo `script.txt` en el directorio actual del cual leerá los comandos a ejecutar. Para utilizar un archivo con una ruta alternativa se puede pasar como parámetro `--script=[path]` donde `[path]` es la dirección del archivo.

### Configuración

La app utiliza determinados valores configurables en la simulación especificados en la orden del proyecto, estos tienen un valor por defecto el cual puede sobreescribirse de distintas formas.
+ La aplicación buscará un archivo `config.txt` en el directorio actual el cual tendrá lineas con el formato `[key]=[value]` sobrescribiendo los valores por defecto para esa llave. Se puede definir una ruta alternativa ejecutando el script con el parámetro `--config=[path]` donde `[path]` es la dirección del archivo alternativo en el que buscar la configuración.
+ Se puede ejecutar el script pasando una serie de parámetros `--[key]=[value]` los cuales sobrescriben los valores, incluso los ya cambiados en el archivo de configuración que se leyó.

### Output

La app crea(si no existe ya) un directorio `output` en el directorio de trabajo actual y escribe un archivo por cada elemento de la simulación informando de toda la información que envía y recibe. Se puede seleccionar un directorio distinto en el que escribir la salida con el parámetro `--output=[path]`.

*NOTA: Para más detalle de la implementación de cada capa buscar en la carpeta* `docs` *el archivo correspondiente a la capa implementada con los detalles de la implementación*