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

function check(obj, name) {
    const v = obj.uniforms[name];
    return v !== undefined && v !== null;
}

function call_with_null(func) {
    return func(null);
}

export { get, set, check, call_with_null }
