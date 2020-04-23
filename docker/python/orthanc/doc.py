# inspect the python API of the "orthanc" module
import inspect
import orthanc
import numbers

def InspectOrthancModule():
    for (name, obj) in inspect.getmembers(orthanc):
        if inspect.isroutine(obj):
            print('Function %s():\n  Documentation: %s\n' % (name, inspect.getdoc(obj)))

        elif inspect.isclass(obj):
            print('Class %s:\n  Documentation: %s' % (name, inspect.getdoc(obj)))

            # Loop over the members of the class
            for (subname, subobj) in inspect.getmembers(obj):
                if isinstance(subobj, numbers.Number):
                    print('  - Enumeration value %s: %s' % (subname, subobj))
                elif (not subname.startswith('_') and
                    inspect.ismethoddescriptor(subobj)):
                    print('  - Method %s(): %s' % (subname, inspect.getdoc(subobj)))
            print('')