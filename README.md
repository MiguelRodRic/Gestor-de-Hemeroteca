# Gestor de Hemeroteca

The aim of the project is to develop a web application where a user will be able to store a set of news obtained from different media and with different formats (whether it is a web page, a PDF file or a XML file) so that it can become a Newspaper Library. In addition, the user can label those news according to different aspects and data mining will be used in order to predict labels for incoming news.

To tackle this task, some research was previously carried out in order to choose the most suitable technologies to the established objectives, both in the case of the tools for creating the application and the NoSQL database, as well as the tools related to the text analysis that is going to undertake the predictions. The main chosen tools are Flask, MongoDB, Scikit-Learn and Lime.

Taking into consideration that the application is not going to be used by the programmer who coded it, the accessibility of the application itself was very important, so that the unprepared final user won't experiment a tough training process.

Finally, the possibility of the user watching the criteria used by the prediction tool when returning a label has been implemented using machine learning techniques. The aim is that the user starts off with storing a set of labeled news and, having done that, the news following those will be labeled by the prediction tool.
