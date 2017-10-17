library(dplyr)

args <- read.csv('../args.csv', stringsAsFactors=FALSE)

tick_infos <- read.csv("tick_infos.csv")
tick_infos <- tick_infos %>% arrange(actual_start) %>% mutate(end = actual_start + duration)
write.csv(tick_infos, 'tick_infos.csv', row.names=FALSE, quote=FALSE)

ticks            <- readLines(file('../ticks.csv'))
if (args$skip_ticks == 0){
  analysed_tick_infos <- tick_infos
  analysed_ticks      <- ticks
} else {
  analysed_tick_infos <- head(tail(tick_infos, -args$skip_ticks), -args$skip_ticks)
  analysed_ticks      <- head(tail(ticks, -args$skip_ticks), -args$skip_ticks)
}
write.csv(analysed_tick_infos, 'analysed_tick_infos.csv', row.names=FALSE, quote=FALSE)
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
