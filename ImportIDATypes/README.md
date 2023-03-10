# Import IDA Types into Ghidra

This guide will tell you how to transfer IDA's type into Ghidra. 

Maybe you are confused why we want to do this, and here's some possible scenario:

- Make Ghidra support ObjC class reconstructing
- Migrate from IDA to Ghidra

Now, let's start!

## 1. Process the TIL
- Unpack IDB, Get the *.til File
- Extract Header from til file:
    ```
    {TILIB64} -#- XXX.til
    {TILIB64} -lc XXX.til > XXX.til.h
    ```

## 2. Convert Header to compilable one
```
GHIDRA=1 python3 idatil2c/idatil2c.py XXX.til.h XXX.til_til2c.h
```

During this step, because some invalid typenames, the script can fail, And you will need to manually fix them :(

- Example:

    ```
    ErrorLine: union _)(_ {int var0[64];unsigned __int8 var1[16];unsigned int var2;char var3[256];char var4[256];int var5;char var6[256];char var7[256];char var8[256];char var9[64];int var10;unsigned int var11;char var12[32];_444B151E9DB59C52BCB6A019F1A5E98A var13;int var14;};
    Traceback (most recent call last):
      File "/mnt/d/Workspaces/UtilWorkspace/Reverse/IDAPlugins/idatil2c/idatil2c.py", line 799, in <module>
        main(sys.argv[1:])
      File "/mnt/d/Workspaces/UtilWorkspace/Reverse/IDAPlugins/idatil2c/idatil2c.py", line 795, in main
        gen_ctypes(args[0], args[1], args[2:])
      File "/mnt/d/Workspaces/UtilWorkspace/Reverse/IDAPlugins/idatil2c/idatil2c.py", line 788, in gen_ctypes
        gen_ctypes_cpp(hdrLoc, outCpp, depends)
      File "/mnt/d/Workspaces/UtilWorkspace/Reverse/IDAPlugins/idatil2c/idatil2c.py", line 681, in gen_ctypes_cpp
        type_defs, ignoredLines = parseDecls(types)
      File "/mnt/d/Workspaces/UtilWorkspace/Reverse/IDAPlugins/idatil2c/idatil2c.py", line 267, in parseDecls
        match = re.findall(r'^union (%s)(;| {)' % IDENTIFIER_PAT, _line)[0][0]
    IndexError: list index out of range
    ```

    - It's easy to see that it's because this union is having a invalid name `_)(_`, usually because obfuscation.
    
    - As `_)(_` is not common name, we can then global replace `_)(_` into something like `_XXX_XXX_`, and rerun the script afterwards.


## 3. Parse the generated source using Ghidra's `Parse C Source`

1. Find what type libraries are used in IDA
    - Press Shift-F11, and record library names in it
        - In my cases, they are `macos11_sdk00_arm64` and `iphoneos64_sdk14`
   
2. Find the path of IDA GDT & GDT Source:
    - GhidraMod users: $GHIDRA_HOME/Ghidra/Features/Base/data/typeinfo/idatil
    - Other users: Download https://github.com/NyaMisty/ghidra_ida_til
3. Find corresponding Type Library `XXX.gdt` and `XXX.til.h` in above path
    - For example I'll have to use:
        - `arm/macos11_sdk00_arm64.gdt` `arm/macos11_sdk00_arm64.til.h`
        - `arm/iphoneos64_sdk14.gdt` `arm/iphoneos64_sdk14.til.h`
4. Import GDT into Ghidra
    - GhidraMod Users: Select GDTs in `Standard Archive` popup menu
    - Other Users: Select GDTs using `Open File Archive..`
5. Compile!
    - Goto `File` -> `Parse C Source...`
    - Click `Clear Profile` button on upper right corner
    - Click plus sign button and add:
        - The `*.til.h` files above
        - The generated `XXX.til_til2c.h`
    - Click `Parse to File...`, and choose a file name like `XXX.gdt`
    - Select `Use Open Archives?` when asked

6. (Debug)
    Sometimes, the parsing would fail (usually because strange struct names).
    Please find the `CParserPlugin.out` file (usually in your home directory), and checkout what's causing the problem.
    
    > Note: Sometimes the error would be wrong/confusing, but the line number&column number that pointing to CParser.out will be ALWAYS correct

    - Example: 

        ```
        C Parser:  Encountered errors during parse.
                 in D:\Workspaces\IDAWorkspace\line_rev\group2_13\LINE_.til_til2c.h near line -60542
        Error: Undefined data type "_"
                 near token: null
        Possibly Undefined : _
                 Last Valid Datatype: uchar
                 Check around C:\Users\Misty\CParserPlugin.out around line: 102867
        
        
        CParser Messages:
        Bad structure size var13  length=0
           In file D:\Workspaces\IDAWorkspace\line_rev\group2_13\LINE_.til_til2c.h
          Near datatype: void
                 in D:\Workspaces\IDAWorkspace\line_rev\group2_13\LINE_.til_til2c.h near line 35413
        ```
        - In this example, the `CParser Messages` part is just a warning, and **you should find parts starts with `Error: `**
        - As you can see, the line number of original file is obviously wrong, so we must instead check `CParserPlugin.out:102867`:
            ```
            struct _1DAC6DA07841E716C70F541FC596288B {_)(_ *var0;char var1[256];...
            ```
        - We can either delete this type (if it's not depended), or fix the invalid name
            - In this example, we choose to replace `_)(_` to `_XXX_XXX_` again as there's multiple use of `_)(_`

## 4. Import and Overwrite original types using GDT's type

1. In Ghidra, Open the generated GDT file (e.g. `XXX.gdt`) with `Open File Archive...`.

2. Right the opened archive, and click `Open For Editing`

3. Move All Types in category `XXX.til_til2c.h` into root level
    - Select all types under category using `Shift` + Mouse Clicking
    - Right click, select `Cut`
    - Right click the archive root node (XXX), select `Paste`

4. Run the Python Script (Using `Script Manager`)
    - Create a new script and copy all content of `ImportGDTTypes.py` into it.
    - Run the script
        - In first question, Choose the 'XXX' library
        - Then choose to import all types or only update existing types (I prefer importing all because that get rids of standalone GDT file)

