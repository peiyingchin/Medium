library(dplyr)
# import library
library("ggplot2")
library('officer') # Load
library(flextable)

# Defined Path
path <- "C:/Users/CHIN/Downloads/medium_dev/Generate report using R"
setwd(path)
# read data
Credit_card <- read.csv(file = 'Credit card transactions - India - Simple.csv')

# create a document
doc <- read_docx() 

# Add a title
doc <-doc %>% body_add_par("Top 15 city spending in total amount transaction", style = 'heading 1') 


# group by city get total for bar chart
df_by_city <-Credit_card  %>% group_by(City) %>% summarise (Total_amount = sum(Amount))

# create a temp file
src <- tempfile(fileext = ".png")
# create PNG object
png(filename = src, width = 4, height = 4, units = 'in', res = 400)

top_fifty <- df_by_city  %>%
  filter(rank(desc(Total_amount))<=15) %>%
  arrange(desc(Total_amount))

# ggplot2 plot with modified x-axis labels

ggplot(top_fifty,  aes(City, Total_amount)) +    
  geom_bar(stat = "identity") + 
  theme(axis.text.x = element_text(angle = 90, size = 10))
# save PNG file
dev.off()

# add PNG image to Word document
doc <-doc %>% body_add_img(src = src, width = 4, height = 4, style = "centered") 

table <- flextable(top_fifty)

# create table title and insert table
doc <- doc %>%body_add_par(" Top 15 spending summarize", style = 'table title')%>%
  body_add_flextable(width(table, width = 2))



print(doc, target = "sample_file.docx")
