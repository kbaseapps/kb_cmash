/*
A KBase module: kb_cmash
*/

module kb_cmash {

    typedef stucture {
        string workspace_name;
        string ref;
        string db;
    } kb_cmash_params

    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kb_cmash(kb_cmash_params params) returns (ReportResults output) authentication required;

};
