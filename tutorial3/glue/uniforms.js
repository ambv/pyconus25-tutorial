/* This is needed in Pyodide, not in MicroPython. 
 *
 * Use in Python like:
 *   uniforms.get(fxaa.material, "resolution").x = ...
 */
function get(obj, name) {
    return obj.uniforms[name].value;
}

function set(obj, name, value) {
    obj.uniforms[name].value = value;
}

export { get, set }