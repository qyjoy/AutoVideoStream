# 获取所有视频文件
$files = Get-ChildItem -Include *.webm, *.mp4, *.mkv -Recurse | Where-Object { -not $_.PSIsContainer }

# 累加时长（单位：秒）
$sum = ($files | ForEach-Object {
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $_.FullName
} | Measure-Object -Sum).Sum

# 输出格式：秒、小时（保留两位小数）
"$sum 秒，共 {0:N2} 小时" -f ($sum / 3600)




# 获取所有目标格式的视频文件
$files = Get-ChildItem -Include *.mkv, *.mp4, *.webm -Recurse | Where-Object { -not $_.PSIsContainer }

# 统计总大小（KB）
$totalSizeKB = ($files | Measure-Object -Property Length -Sum).Sum / 1024

# 统计总时长（秒）
$totalDurationSec = ($files | ForEach-Object {
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $_.FullName
} | Measure-Object -Sum).Sum

# 计算平均码率
if ($totalDurationSec -eq 0) {
    "总时长为 0，无法计算平均码率"
} else {
    $avgBitrate = ($totalSizeKB * 8) / $totalDurationSec
    "平均码率: {0:N2} kbps" -f $avgBitrate
}