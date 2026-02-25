using System;
using UnityEditor;
using UnityEditor.Build.Reporting;

namespace BuildAutomation
{
    public static class BuildScript
    {
        public static void BuildAndroid()
        {
            string outputPath = Environment.GetEnvironmentVariable("BUILD_OUTPUT_PATH");
            string scenesEnv = Environment.GetEnvironmentVariable("BUILD_SCENES");

            if (string.IsNullOrEmpty(outputPath))
            {
                Console.Error.WriteLine("BUILD_OUTPUT_PATH environment variable not set.");
                EditorApplication.Exit(1);
                return;
            }

            if (string.IsNullOrEmpty(scenesEnv))
            {
                Console.Error.WriteLine("BUILD_SCENES environment variable not set.");
                EditorApplication.Exit(1);
                return;
            }

            string[] scenes = scenesEnv.Split(';');

            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = outputPath,
                target = BuildTarget.Android,
                options = BuildOptions.None
            };

            Console.WriteLine($"Building Android APK: {outputPath}");
            Console.WriteLine($"Scenes: {scenesEnv}");

            BuildReport report = BuildPipeline.BuildPlayer(options);
            BuildSummary summary = report.summary;

            if (summary.result == BuildResult.Succeeded)
            {
                Console.WriteLine($"Build succeeded: {summary.totalSize} bytes");
                EditorApplication.Exit(0);
            }
            else
            {
                Console.Error.WriteLine($"Build failed: {summary.result}");
                EditorApplication.Exit(1);
            }
        }
    }
}
