import { Avatar, Card, CardBody, CardFooter, CardHeader, KindBadge, Tag } from '@lanterngrid/ui'

/** Static example of a feed post, used on the landing page and in the UI kit. */
export function SamplePost() {
  return (
    <Card raised>
      <CardHeader>
        <Avatar name="Ada Park" />
        <div className="leading-tight">
          <div className="font-semibold">Ada Park</div>
          <div className="font-mono text-xs text-ink-3">@adapark · 2h</div>
        </div>
        <KindBadge kind="snippet" className="ml-auto" />
      </CardHeader>
      <CardBody>
        <p>Finally got keyset pagination feeling instant. No more OFFSET.</p>
        <pre className="overflow-x-auto border border-line bg-[#0c1017] p-3 font-mono text-[13px] leading-relaxed text-[#e8edf4]">
          <span className="text-[#ff4f97]">select</span> *{' '}
          <span className="text-[#ff4f97]">from</span> posts{'\n'}
          <span className="text-[#ff4f97]">where</span> author_id ={' '}
          <span className="text-[#ff4f97]">any</span>(
          <span className="text-[#2fd4f5]">:friends</span>){'\n  '}
          <span className="text-[#ff4f97]">and</span> id &lt;{' '}
          <span className="text-[#2fd4f5]">:cursor</span>
          {'  '}
          <span className="text-[#8491a3]">-- uuidv7</span>
          {'\n'}
          <span className="text-[#ff4f97]">order by</span> id{' '}
          <span className="text-[#ff4f97]">desc limit</span>{' '}
          <span className="text-[#8edb3f]">20</span>;
        </pre>
        <div className="flex flex-wrap gap-1.5">
          <Tag name="postgres" />
          <Tag name="performance" />
        </div>
      </CardBody>
      <CardFooter>
        <span>▲ 42</span>
        <span>12 comments</span>
        <span>share</span>
      </CardFooter>
    </Card>
  )
}
