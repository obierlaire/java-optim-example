import org.apache.commons.io.FileUtils

/**
 * Reads Java source code from files using Apache Commons IO
 */
class SourceReader {
    
    /**
     * Finds source code for a specific line in a Java class
     * @param className - Full Java class name (e.g., "com.example.MyClass")
     * @param lineNumber - Line number where CPU hotspot was detected
     * @param sourcePath - Base path to search for source files (e.g., "target")
     * @return [sourceCode, filePath] - The actual code line and its full path
     */
    static findSourceCode(String className, int lineNumber, String sourcePath) {
        // Convert class name to file path: com.example.MyClass -> com/example/MyClass.java
        def javaFile = "${className.replace('.', '/')}.java"
        def fullPath = "${sourcePath}/src/main/java/${javaFile}"
        
        def sourceFile = new File(fullPath)
        if (!sourceFile.exists()) {
            def simpleClassName = className.tokenize('.').last()
            return ["<source not found>", "${simpleClassName}.java"]
        }
        
        def lines = FileUtils.readLines(sourceFile, "UTF-8")
        if (lineNumber > 0 && lineNumber <= lines.size()) {
            def actualCode = lines[lineNumber - 1].trim()
            return [actualCode, fullPath]
        }
        
        return ["<line not found>", fullPath]
    }
}