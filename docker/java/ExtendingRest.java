import be.uclouvain.orthanc.Callbacks;
import be.uclouvain.orthanc.HttpMethod;
import be.uclouvain.orthanc.RestOutput;

import java.util.Map;

public class ExtendingRest {
    static {
        Callbacks.register("/java", new Callbacks.OnRestRequest() {
            @Override
            public void call(RestOutput output,
                             HttpMethod method,
                             String uri,
                             String[] regularExpressionGroups,
                             Map<String, String> headers,
                             Map<String, String> getParameters,
                             byte[] body) {
                output.answerBuffer("Hello from Java!\n".getBytes(), "text/plain");
            }
        });
    }
}