library(dplyr)

args <- read.csv('../args.csv', stringsAsFactors=FALSE)

tick_infos <- read.csv("tick_infos.csv")
tick_infos <- tick_infos %>% arrange(actual_start) %>% mutate(end = actual_start + duration)
write.csv(tick_infos, 'tick_infos.csv', row.names=FALSE, quote=FALSE)

skip_ticks            <- ceiling(max(
  ifelse(args$blocks_per_tick == 0, 0, 1/args$blocks_per_tick),
  ifelse(args$txs_per_tick == 0, 0, 1/args$txs_per_tick),
  1/args$tick_duration)
)
analysed_tick_infos   <- head(tail(tick_infos, -skip_ticks), -skip_ticks)
write.csv(analysed_tick_infos, 'analysed_tick_infos.csv', row.names=FALSE, quote=FALSE)

ticks            <- readLines(file('../ticks.csv'))
analysed_ticks   <- head(tail(ticks, -skip_ticks), -skip_ticks)
write(analysed_ticks, 'analysed_ticks.csv')

files = c("blocks_create", "blocks_stats", "txs")
for (i in 1:length(files)) {
  data <- read.csv(paste(files[i], '_raw.csv', sep = ''))
  data <- data %>%
    arrange(timestamp) %>%
    filter(timestamp > head(analysed_tick_infos$actual_start, 1) & timestamp < tail(analysed_tick_infos$end, 1))
  write.csv(data, paste(files[i], 'csv', sep = '.'), row.names=FALSE, quote=FALSE)
}

files = c("blocks_reconstructed", "txs_received", "blocks_received", "peer_logic_validation", "update_tip")
for (i in 1:length(files)) {
  data <- read.csv(paste(files[i], '_raw.csv', sep = ''))
  data <- data %>%
    arrange(timestamp) %>%
    filter(timestamp > head(analysed_tick_infos$actual_start, 1))
  write.csv(data, paste(files[i], 'csv', sep = '.'), row.names=FALSE, quote=FALSE)
}
