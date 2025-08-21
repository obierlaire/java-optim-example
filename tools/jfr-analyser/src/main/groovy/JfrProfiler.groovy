import com.google.gson.GsonBuilder
import picocli.CommandLine
import picocli.CommandLine.*
import java.util.concurrent.Callable

/**
 * JFR CPU Profiler
 * 
 * Simple tool to analyze Java Flight Recorder files and identify:
 * - Which lines of code use the most CPU
 * - The actual source code at those lines
 * - CPU percentage for each hotspot
 * 
 * Usage: java -jar jfr-profiler.jar recording.jfr com.myapp output.json
 */
@Command(name = "jfr-profiler", 
         mixinStandardHelpOptions = true,
         version = "1.0.0",
         description = "Find CPU hotspots in Java Flight Recorder files")
class JfrProfiler implements Callable<Integer> {
    
    @Parameters(index = "0", description = "JFR recording file")
    String jfrFile
    
    @Parameters(index = "1", description = "Package to analyze (e.g., com.myapp)")  
    String packageFilter
    
    @Parameters(index = "2", description = "Output JSON file")
    String outputFile
    
    @Option(names = ["-s", "--source-path"], 
            description = "Source directory (auto-detected if not provided)")
    String sourcePath

    Integer call() {
        println "🔍 Analyzing JFR file: $jfrFile"
        println "📦 Package filter: $packageFilter"
        
        // Auto-detect source directory if not provided
        if (!sourcePath) {
            sourcePath = autoDetectSources()
            println "📁 Auto-detected sources: $sourcePath"
        }
        
        // Find CPU hotspots
        def hotspots = HotspotFinder.findHotspots(jfrFile, packageFilter, sourcePath)
        
        // Create result
        def result = [
            hotspots: hotspots,
            totalSamples: hotspots.sum { it.cpuPercent } ? hotspots.size() : 0,
            analysis: [
                packageFilter: packageFilter,
                generatedAt: new Date().toString()
            ]
        ]
        
        // Write JSON result
        def gson = new GsonBuilder().setPrettyPrinting().create()
        new File(outputFile).text = gson.toJson(result)
        
        // Print summary
        println "\n✅ Analysis complete!"
        println "📄 Results: $outputFile"
        println "🔥 Found ${hotspots.size()} hotspots"
        
        println "\n🏆 Top CPU Hotspots:"
        hotspots.take(5).eachWithIndex { hotspot, i ->
            printf "%d. %s:%d (%.2f%%) - %s\n", 
                i+1, hotspot.filePath, hotspot.line, hotspot.cpuPercent, hotspot.method
        }
        
        return 0
    }
    
    /**
     * Auto-detect where source files are located
     * Common build tools put sources in target/ or build/ directories
     */
    private String autoDetectSources() {
        def candidates = ["target", "build", "out"]
        
        def found = candidates.find { dir ->
            new File("${dir}/src/main/java").exists()
        }
        
        return found ?: "." // Default to current directory if nothing found
    }
    
    static void main(String[] args) {
        System.exit(new CommandLine(new JfrProfiler()).execute(args))
    }
}