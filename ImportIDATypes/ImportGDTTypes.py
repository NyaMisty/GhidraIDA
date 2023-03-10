# ReLinkObjCTypes.py
#@author NyaMisty
#@category Helper
#@keybinding 
#@menupath 
#@toolbar 

# Black magic to forcefully update linked types from another GDT, even the GDT changed

tool = state.getTool()
programDtm = currentProgram.getDataTypeManager()

dtmPlugin = [c for c in tool.getManagedPlugins() if 'DataTypeManagerPlugin' in repr(c)][0]
dtmHandler = dtmPlugin.getDataTypeManagerHandler()

# Choose the archive that going to be imported
archives = dtmPlugin.getAllArchives()
choice = askChoices("Choose datatype archive", "", range(len(archives)), [ '%s (%s)' % (c.name, repr(c)) for c in dtmPlugin.getAllArchives()])
print(choice)
archive = archives[choice[0]]
dtm = archive.getDataTypeManager()

# Begin importing!

isImportAll = askYesNo("Import all types?", 
    "Choose Import Method:\n"
    "Yes: import all types in GDT\n"
    "No: only update existing types"
)

from ghidra.program.model.data import CategoryPath
from ghidra.app.plugin.core.datamgr import DataTypeSynchronizer

if isImportAll: # Import all types in the new GDT
    types = dtm.getCategory(CategoryPath('/')).getDataTypes()
    def importType(t):
        if not t.sourceArchive.getSourceArchiveID() == dtm.getUniversalID(): # exclude builtin types like float / int ...
            return
        print("Importing %s" % t.name)
        DataTypeSynchronizer.update(programDtm, t)
else:     # Update only existing type from new GDT
    types = programDtm.getCategory(CategoryPath('/')).getDataTypes()
    def importType(t):
        if not t.sourceArchive.getSourceArchiveID() == programDtm.getUniversalID(): # exclude builtin types like float / int ...
            return
        tt = dtm.getDataType('/' + t.name)
        if tt:
            print("Importing %s" % tt.name)
            DataTypeSynchronizer.update(programDtm, tt)


monitor.initialize(len(types))
for t in types:
    monitor.checkCanceled() # check to see if the user clicked cancel
    monitor.incrementProgress(1) # update the progress
    monitor.setMessage("Working on " + str(t.name)) # update the status message
    importType(t)