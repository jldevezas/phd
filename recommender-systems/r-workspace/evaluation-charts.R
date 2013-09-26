#
# Evaluation Chart Plotting
# José Devezas (joseluisdevezas@gmail.com)
#
# Chart plotting that goes with the jld.py library evaluation results.
#

# evaluation.filename   CSV with at least two columns: the number of features and the average mean absolute error.
# output.filename       PDF file to store the plotted chart.
# max.x                 Right limit of the X axis (in some cases the MAE stabilizes and we don't need to see more).
# width                 Width in points of the plotted chart.
# height                Height in points of the plotted chart.
PlotFeatureSizeMae <- function(evaluation.filename, output.filename, max.x=NULL, width=12, height=4) {
  if (!require(ggplot2)) {
    install.packages("ggplot2")
    library(ggplot2)
  }
  
  d <- read.csv(evaluation.filename)
  if (!is.null(max.x)) {
    d <- d[which(d$features <= max.x), ]
  }
  
  y.margin <- (max(d$avg.mae)-min(d$avg.mae)) / 10
  chart <- ggplot(d, aes(x=features, y=avg.mae)) +
    geom_line() +
    geom_point() +
    geom_point(data=d[which.min(d$avg.mae), ], color="steelblue", size=4) +
    geom_text(data=d[which.min(d$avg.mae), ], aes(label=paste("ArgMin(Avg. MAE)", features, sep=" = ")),
              color="steelblue", hjust=-0.05, vjust=1.5) +
    scale_y_continuous(limits=c(min(d$avg.mae) - y.margin, max(d$avg.mae))) +
    labs(x="Number of Latent Factors", y="Average Mean Absolute Error")
  
  ggsave(filename=output.filename, width=width, height=height)
}

PlotFeatureSizeMae("~/Desktop/lastfm-jld-dataset/output/eval.csv",
                   "~/Desktop/feature_size_mae.pdf",
                   max.x=500, width=8, height=4)

PlotFeatureSizeMae("~/Desktop/lastfm-jld-dataset/output/eval.csv",
                   "~/Desktop/feature_size_mae.pdf",
                   max.x=500, width=5, height=3.5)

PlotFeatureSizeMae("~/Desktop/lastfm-jld-dataset/output/eval.csv",
                   "~/Desktop/feature_size_mae.png",
                   max.x=500, width=6, height=4.2)