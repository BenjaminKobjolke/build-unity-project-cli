using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace BuildAutomation
{
    [InitializeOnLoad]
    public static class BuildTriggerWatcher
    {
        private static readonly string TriggerFilename = "build_trigger.json";
        private static readonly string ResultFilename = "build_result.json";

        static BuildTriggerWatcher()
        {
            EditorApplication.update += PollForTrigger;
        }

        private static void PollForTrigger()
        {
            string projectRoot = Path.GetDirectoryName(Application.dataPath);
            string triggerPath = Path.Combine(projectRoot, TriggerFilename);

            if (!File.Exists(triggerPath))
                return;

            string json = File.ReadAllText(triggerPath);
            File.Delete(triggerPath);

            TriggerData trigger = JsonUtility.FromJson<TriggerData>(json);
            ExecuteBuild(projectRoot, trigger);
        }

        private static void ExecuteBuild(string projectRoot, TriggerData trigger)
        {
            string resultPath = Path.Combine(projectRoot, ResultFilename);
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();

            try
            {
                BuildPlayerOptions options = new BuildPlayerOptions
                {
                    scenes = trigger.scenes,
                    locationPathName = trigger.output_path,
                    target = (BuildTarget)Enum.Parse(typeof(BuildTarget), trigger.build_target),
                    options = BuildOptions.None
                };

                Debug.Log($"[BuildTriggerWatcher] Building: {trigger.output_path}");
                BuildReport report = BuildPipeline.BuildPlayer(options);
                stopwatch.Stop();

                bool success = report.summary.result == BuildResult.Succeeded;
                string error = success ? "" : report.summary.result.ToString();

                WriteResult(resultPath, success, error, stopwatch.Elapsed.TotalSeconds);
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                WriteResult(resultPath, false, ex.Message, stopwatch.Elapsed.TotalSeconds);
            }
        }

        private static void WriteResult(string path, bool success, string error, double durationSeconds)
        {
            ResultData result = new ResultData
            {
                success = success,
                error = error,
                duration_seconds = (float)durationSeconds
            };
            string json = JsonUtility.ToJson(result, true);
            File.WriteAllText(path, json);
            Debug.Log($"[BuildTriggerWatcher] Result written: success={success}");
        }

        [Serializable]
        private class TriggerData
        {
            public string output_path;
            public string[] scenes;
            public string build_target;
        }

        [Serializable]
        private class ResultData
        {
            public bool success;
            public string error;
            public float duration_seconds;
        }
    }
}
