function IncomingWorklistRequestFilter(query, origin)
  -- PrintRecursive(query)
  -- PrintRecursive(origin)

  -- If the query has a filter on ScheduledProcedureStepStartTime that looks like XXXXXX-XXXXXX
  -- because it is supposed to be combined with the ScheduledProcedureStepStartDate, remove the filter
  -- on the time because Orthanc does not handle it correctly right now.
  -- sample:  findscu -v -W --aetitle STORESCU -k "PatientName=" -k "(0040,0100)[0].Modality=DX" -k "(0040,0100)[0].ScheduledProcedureStepStartDate=20260108-20260110" -k "(0040,0100)[0].ScheduledProcedureStepStartTime=101237-101237" localhost 4243

  if query['0040,0100'] and query['0040,0100'][1] and query['0040,0100'][1]['0040,0003'] then
    query['0040,0100'][1]['0040,0003'] = nil
  end

  return query
end