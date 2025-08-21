import jdk.jfr.consumer.*
import java.nio.file.Paths

/**
 * Analyzes JFR (Java Flight Recorder) files to find CPU hotspots
 * 
 * JFR Records:
 * - ExecutionSample: Shows where CPU was spending time when sampled
 * - StackTrace: Call stack at that moment  
 * - Frame: Single method call with line number
 */
class HotspotFinder {
    
    /**
     * Finds CPU hotspots in a JFR recording
     * @param jfrFile - Path to .jfr file
     * @param packageFilter - Only analyze classes in this package (e.g., "com.myapp")
     * @param sourcePath - Where to find source files
     * @return List of hotspots with CPU percentages
     */
    static findHotspots(String jfrFile, String packageFilter, String sourcePath) {
        
        // Count how many times each line appears in CPU samples
        def lineCounts = [:]
        def lineDetails = [:]  // Store method names and source code
        def totalSamples = 0
        
        // Read the JFR file
        new RecordingFile(Paths.get(jfrFile)).withCloseable { recording ->
            while (recording.hasMoreEvents()) {
                def event = recording.readEvent()
                
                // We only care about CPU execution samples
                if (event.eventType.name == "jdk.ExecutionSample") {
                    
                    // Look at the call stack when CPU sample was taken
                    def stack = event.stackTrace
                    if (stack?.frames) {
                        
                        // Find the first frame (top of stack) that matches our package
                        def hotFrame = stack.frames.find { frame ->
                            def method = frame.method
                            def className = method?.type?.name
                            
                            // Only analyze our application code, skip JVM internals
                            return className?.contains(packageFilter) && frame.lineNumber > 0
                        }
                        
                        if (hotFrame) {
                            def className = hotFrame.method.type.name
                            def simpleClassName = className.tokenize('.').last()
                            def methodName = hotFrame.method.name
                            def lineNumber = hotFrame.lineNumber
                            
                            // Create unique key for this line
                            def key = "${simpleClassName}:${lineNumber}"
                            
                            // Count this occurrence
                            lineCounts[key] = (lineCounts[key] ?: 0) + 1
                            
                            // Store details (method name and source code)
                            if (!lineDetails[key]) {
                                def (sourceCode, filePath) = SourceReader.findSourceCode(
                                    className, lineNumber, sourcePath)
                                lineDetails[key] = [
                                    method: methodName,
                                    filePath: filePath,
                                    code: sourceCode
                                ]
                            }
                            
                            totalSamples++
                        }
                    }
                }
            }
        }
        
        // Convert counts to percentages and create final list
        def hotspots = []
        lineCounts.each { key, count ->
            def details = lineDetails[key]
            def cpuPercent = (count * 100.0 / totalSamples).round(2)
            
            hotspots << [
                cpuPercent: cpuPercent,
                filePath: details.filePath.toString(),
                line: Integer.parseInt(key.split(':')[1]),
                method: details.method.toString(),
                code: details.code.toString()
            ]
        }
        
        // Sort by CPU usage (highest first)
        return hotspots.sort { -it.cpuPercent }
    }
}